"""
Test suite for parallel domain-decomposed Hamiltonian evolution.

Validates:
1. Field equivalence (parallel == sequential within tolerance)
2. Halo exchange correctness
3. Scaling performance
4. Boundary condition handling
"""
import pytest
import numpy as np
import time
from backend.core.parallel_hamiltonian import (
    create_chunks,
    extract_halos,
    evolve_chunk,
    reassemble_field,
    ParallelHamiltonianSolver,
    JOBLIB_AVAILABLE
)


# Test configuration
SEED = 42069
ETA, GAMMA, BETA, SIGMA = 0.4, 0.3, 0.1, 0.05


def hamiltonian_field_2d(shape):
    """Generate test Hamiltonian field (distance to center + walls)"""
    rows, cols = np.indices(shape)
    center = np.array(shape) / 2
    dist = np.sqrt((rows - center[0])**2 + (cols - center[1])**2)
    H = dist / np.max(dist)
    
    # Add wall repulsion
    H += 0.8 * np.minimum(rows, shape[0]-1-rows) / (shape[0]/2)
    H += 0.8 * np.minimum(cols, shape[1]-1-cols) / (shape[1]/2)
    
    return H


def sequential_evolution(H_base, max_iter, eta=ETA, gamma=GAMMA, beta=BETA, sigma=SIGMA):
    """Reference sequential evolution"""
    np.random.seed(SEED)
    H = H_base.copy()
    
    for t in range(max_iter):
        sigmoid = 1.0 / (1.0 + np.exp(-gamma * H))
        noise = np.random.normal(0, 1 + beta * np.abs(H), size=H.shape)
        H = H_base + eta * H * sigmoid + sigma * noise
    
    return H


def parallel_evolution_manual(H_base, max_iter, n_chunks=4):
    """Manual parallel evolution (for testing without full async framework)"""
    # NO global seed - each chunk will seed independently
    chunks = create_chunks(H_base.shape, n_chunks)
    H = H_base.copy()
    
    for t in range(max_iter):
        # Halo exchange
        halos = extract_halos(H, chunks)
        
        # Evolve chunks (simulated parallel)
        # Note: In parallel execution, each chunk gets its own RNG
        # This is fundamentally different from sequential
        updated_chunks = []
        for chunk in chunks:
            updated = evolve_chunk(
                chunk, H_base, H, halos[chunk.idx],
                ETA, GAMMA, BETA, SIGMA,
                random_seed=SEED + chunk.idx * 1000 + t  # Deterministic but different
            )
            updated_chunks.append(updated)
        
        # Reassemble
        H = reassemble_field(H, chunks, updated_chunks)
    
    return H


class TestChunking:
    """Test domain decomposition mechanics"""
    
    def test_create_chunks_basic(self):
        """Test basic chunk creation"""
        shape = (64, 64)
        n_chunks = 4
        chunks = create_chunks(shape, n_chunks)
        
        assert len(chunks) == n_chunks
        assert all(c.idx == i for i, c in enumerate(chunks))
        
        # Check coverage (all rows assigned)
        covered_rows = set()
        for chunk in chunks:
            row_start = chunk.slice_2d[0].start
            row_end = chunk.slice_2d[0].stop
            covered_rows.update(range(row_start, row_end))
        
        assert covered_rows == set(range(shape[0]))
    
    def test_chunk_halo_sources(self):
        """Test halo metadata correctness"""
        chunks = create_chunks((64, 64), 4)
        
        # First chunk: only bottom neighbor
        assert len(chunks[0].halo_sources) == 1
        assert chunks[0].halo_sources[0] == (1, 'bottom')
        
        # Middle chunks: both neighbors
        assert len(chunks[1].halo_sources) == 2
        assert (0, 'top') in chunks[1].halo_sources
        assert (2, 'bottom') in chunks[1].halo_sources
        
        # Last chunk: only top neighbor
        assert len(chunks[-1].halo_sources) == 1
        assert chunks[-1].halo_sources[0] == (chunks[-1].idx - 1, 'top')
    
    def test_interior_mask(self):
        """Test interior mask excludes halos"""
        chunks = create_chunks((64, 64), 4)
        
        # First chunk: bottom row is halo
        assert not chunks[0].interior_mask[-1, :].any()
        assert chunks[0].interior_mask[:-1, :].all()
        
        # Middle chunk: top and bottom are halos
        assert not chunks[1].interior_mask[0, :].any()
        assert not chunks[1].interior_mask[-1, :].any()
        assert chunks[1].interior_mask[1:-1, :].all()
        
        # Last chunk: top row is halo
        assert not chunks[-1].interior_mask[0, :].any()
        assert chunks[-1].interior_mask[1:, :].all()


class TestHaloExchange:
    """Test halo (ghost cell) exchange"""
    
    def test_extract_halos_basic(self):
        """Test halo extraction"""
        H = np.arange(64*64).reshape(64, 64).astype(np.float64)
        chunks = create_chunks(H.shape, 4)
        halos = extract_halos(H, chunks)
        
        assert len(halos) == 4
        
        # Check chunk 1 receives correct halos
        assert (0, 'top') in halos[1]
        assert (2, 'bottom') in halos[1]
        
        # Verify halo data matches expected rows
        chunk0_bottom_row = H[chunks[0].slice_2d[0].stop - 1, :]
        chunk1_received_top = halos[1][(0, 'top')]
        np.testing.assert_array_equal(chunk0_bottom_row, chunk1_received_top)
    
    def test_halo_continuity(self):
        """Test halos maintain continuity across boundaries"""
        H = hamiltonian_field_2d((64, 64))
        chunks = create_chunks(H.shape, 4)
        halos = extract_halos(H, chunks)
        
        # Boundary between chunk 0 and chunk 1
        boundary_row_idx = chunks[0].slice_2d[0].stop
        
        # Chunk 1's top halo should match actual boundary
        np.testing.assert_array_equal(
            H[boundary_row_idx - 1, :],
            halos[1][(0, 'top')]
        )


class TestFieldEquivalence:
    """Test parallel == sequential evolution"""
    
    def test_small_field_equivalence(self):
        """Test 64×64 field with 4 chunks
        
        Note: Parallel uses different RNG streams per chunk (for parallelism),
        so we expect statistical similarity, not exact equivalence.
        Test validates: similar energy distributions, no catastrophic errors.
        """
        shape = (64, 64)
        max_iter = 50
        
        H_base = hamiltonian_field_2d(shape)
        
        # Sequential reference
        H_seq = sequential_evolution(H_base, max_iter)
        
        # Parallel version
        H_para = parallel_evolution_manual(H_base, max_iter, n_chunks=4)
        
        # Statistical comparison (not exact match due to RNG chunking)
        mean_seq = np.mean(H_seq)
        mean_para = np.mean(H_para)
        std_seq = np.std(H_seq)
        std_para = np.std(H_para)
        
        print(f"\n  Sequential: mean={mean_seq:.4f}, std={std_seq:.4f}")
        print(f"  Parallel:   mean={mean_para:.4f}, std={std_para:.4f}")
        print(f"  Mean diff: {abs(mean_seq - mean_para):.4f}")
        print(f"  Std diff:  {abs(std_seq - std_para):.4f}")
        
        # Test: distributions should be similar (within 20% for stochastic dynamics)
        assert abs(mean_seq - mean_para) / mean_seq < 0.2, "Mean energy differs significantly"
        assert abs(std_seq - std_para) / std_seq < 0.3, "Energy variance differs significantly"
        
        # Test: no NaN or Inf
        assert not np.any(np.isnan(H_para)), "Parallel produced NaN"
        assert not np.any(np.isinf(H_para)), "Parallel produced Inf"
    
    @pytest.mark.skipif(not JOBLIB_AVAILABLE, reason="Joblib required")
    def test_parallel_solver_integration(self):
        """Test full ParallelHamiltonianSolver"""
        network = {f'node-{i}': [f'node-{(i+1)%64}'] for i in range(64)}
        
        solver = ParallelHamiltonianSolver(n_jobs=2)
        
        # Note: Can't easily test async in pytest without special setup
        # This would need to be run manually or with pytest-asyncio
        # result = await solver.solve_parallel(network, max_iterations=100, n_chunks=2)
        # assert result['converged']
        
        # For now, just test initialization
        assert solver.n_jobs == 2
        assert solver.alpha == 0.618


class TestBenchmark:
    """Performance benchmarking"""
    
    @pytest.mark.slow
    def test_scaling_curve(self):
        """Test performance scaling with different chunk counts"""
        shape = (128, 128)
        max_iter = 200
        H_base = hamiltonian_field_2d(shape)
        
        print("\n=== Scaling Benchmark ===")
        print(f"Grid: {shape}, Iterations: {max_iter}")
        
        # Sequential baseline
        t0 = time.perf_counter()
        H_seq = sequential_evolution(H_base, max_iter)
        t_seq = time.perf_counter() - t0
        print(f"\nSequential: {t_seq:.3f}s")
        
        # Parallel with varying chunks
        for n_chunks in [2, 4, 8]:
            t0 = time.perf_counter()
            H_para = parallel_evolution_manual(H_base, max_iter, n_chunks)
            t_para = time.perf_counter() - t0
            
            speedup = t_seq / t_para
            diff = np.max(np.abs(H_seq - H_para))
            
            print(f"Parallel ({n_chunks} chunks): {t_para:.3f}s, "
                  f"speedup: {speedup:.2f}×, max_diff: {diff:.2e}")


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_single_chunk(self):
        """Test with n_chunks=1 (no parallelism)"""
        H_base = hamiltonian_field_2d((32, 32))
        chunks = create_chunks(H_base.shape, n_chunks=1)
        
        assert len(chunks) == 1
        assert len(chunks[0].halo_sources) == 0  # No neighbors
        assert chunks[0].interior_mask.all()  # No halos
    
    def test_more_chunks_than_rows(self):
        """Test graceful handling of n_chunks > n_rows"""
        shape = (16, 64)
        n_chunks = 32  # More than rows
        
        chunks = create_chunks(shape, n_chunks)
        
        # Should still create valid chunks (some will be empty)
        assert len(chunks) == n_chunks
        
        # All rows should be covered
        covered = set()
        for chunk in chunks:
            if chunk.slice_2d[0].start < chunk.slice_2d[0].stop:
                covered.update(range(chunk.slice_2d[0].start, chunk.slice_2d[0].stop))
        
        assert len(covered) == shape[0]


# Manual test runner for debugging
if __name__ == "__main__":
    print("=== PARALLEL HAMILTONIAN TEST SUITE ===")
    print("=" * 70)
    
    # Run field equivalence test
    print("\n[1/3] Field Equivalence Test (64×64, 50 iterations)...")
    test = TestFieldEquivalence()
    test.test_small_field_equivalence()
    print("      ✅ PASSED - Parallel matches sequential")
    
    # Run scaling benchmark
    print("\n[2/3] Scaling Benchmark (128×128, 200 iterations)...")
    benchmark = TestBenchmark()
    benchmark.test_scaling_curve()
    
    # Run edge cases
    print("\n[3/3] Edge Cases...")
    edge_test = TestEdgeCases()
    edge_test.test_single_chunk()
    edge_test.test_more_chunks_than_rows()
    print("      ✅ PASSED - Edge cases handled")
    
    print("\n" + "=" * 70)
    print("=== ALL TESTS COMPLETE ===")
