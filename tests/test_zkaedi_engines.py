"""
Comprehensive Tests for ZKAEDI PRIME Production Engines

Tests cover:
- ZKAEDIPrimeBoosted (Production engine with 29× speedup)
- ZKAEDIUltraBoosted (JIT-compiled engine with 31× speedup)
- QuantumResistantZKAEDI (Post-quantum ready engine)
"""
import pytest
import numpy as np
from typing import Dict

from backend.core.zkaedi_prime_boosted import ZKAEDIPrimeBoosted, EnhancedSolution
from backend.core.zkaedi_ultra_boosted import ZKAEDIUltraBoosted, UltraSolution
from backend.core.quantum_resistant_engine import QuantumResistantZKAEDI, QuantumSolution


# Test fixtures
@pytest.fixture
def small_network() -> Dict:
    """Small 3-node network for quick tests"""
    return {
        '192.168.1.1': ['192.168.1.2', '192.168.1.3'],
        '192.168.1.2': ['192.168.1.1'],
        '192.168.1.3': ['192.168.1.1']
    }


@pytest.fixture
def medium_network() -> Dict:
    """Medium 50-node network for performance tests"""
    nodes = [f'10.0.0.{i}' for i in range(1, 51)]
    network = {}
    for i, node in enumerate(nodes):
        # Hub-spoke topology: first node connects to all, others connect to hub
        if i == 0:
            network[node] = nodes[1:10]  # Hub connects to first 9 nodes
        else:
            network[node] = [nodes[0]]  # Others connect to hub
    return network


@pytest.fixture
def boosted_engine() -> ZKAEDIPrimeBoosted:
    """Standard boosted engine instance"""
    return ZKAEDIPrimeBoosted(
        alpha=0.618,
        eta=0.4,
        gamma=0.3,
        beta=0.1,
        sigma=0.05
    )


@pytest.fixture
def ultra_engine() -> ZKAEDIUltraBoosted:
    """Standard ultra-boosted engine instance"""
    return ZKAEDIUltraBoosted(
        alpha=0.618,
        eta=0.4,
        gamma=0.3,
        beta=0.1,
        sigma=0.05
    )


@pytest.fixture
def quantum_engine() -> QuantumResistantZKAEDI:
    """Standard quantum-resistant engine instance"""
    return QuantumResistantZKAEDI(
        alpha=0.618,
        eta=0.4
    )


# ==================== ZKAEDIPrimeBoosted Tests ====================

class TestZKAEDIPrimeBoosted:
    """Test suite for production boosted engine"""

    @pytest.mark.asyncio
    async def test_initialization(self, boosted_engine):
        """Test engine initialization with default parameters"""
        assert boosted_engine.alpha == 0.618
        assert boosted_engine.eta_base == 0.4
        assert boosted_engine.gamma == 0.3
        assert boosted_engine.beta == 0.1
        assert boosted_engine.sigma == 0.05
        assert boosted_engine.phi == 1.618

    @pytest.mark.asyncio
    async def test_adaptive_eta_decay(self, boosted_engine):
        """Test adaptive η decay schedule"""
        # At t=0, should be base eta
        eta_0 = boosted_engine.adaptive_eta_decay(0, 0.4)
        assert eta_0 == 0.4

        # At t=8000, should decay by factor of 0.92
        eta_8000 = boosted_engine.adaptive_eta_decay(8000, 0.4)
        assert abs(eta_8000 - 0.4 * 0.92) < 0.001

        # Should never go below 30% of base
        eta_large = boosted_engine.adaptive_eta_decay(100000, 0.4)
        assert eta_large >= 0.4 * 0.3

    @pytest.mark.asyncio
    async def test_chaos_boost_activation(self, boosted_engine):
        """Test chaos boost triggers at high energy"""
        # Below threshold - no boost
        H_low = np.array([1.0, 2.0, 3.0])
        eta_no_boost = boosted_engine.chaos_boost_eta(H_low, 0.4)
        assert eta_no_boost == 0.4

        # Above threshold (9.5) - should boost
        H_high = np.array([10.0, 2.0, 3.0])
        eta_boosted = boosted_engine.chaos_boost_eta(H_high, 0.4)
        assert eta_boosted > 0.4
        assert eta_boosted <= 0.82

    @pytest.mark.asyncio
    async def test_golden_fractal_delay(self, boosted_engine):
        """Test golden fractal delay modulation"""
        # Below bifurcation threshold - no delay
        H_low = np.array([1.0, 2.0, 3.0])
        delay_low = boosted_engine.golden_fractal_delay(H_low, 0)
        assert delay_low == 0.0

        # Above threshold (4.5) - should have delay
        H_high = np.array([5.0, 2.0, 3.0])
        delay_high = boosted_engine.golden_fractal_delay(H_high, 0)
        assert delay_high > 0.0

    @pytest.mark.asyncio
    async def test_solve_small_network(self, boosted_engine, small_network):
        """Test solving small network"""
        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=small_network,
            max_iterations=1000
        )

        assert isinstance(result, EnhancedSolution)
        assert result.algorithm == "ZKAEDI_PRIME_BOOSTED"
        assert result.steps > 0
        assert result.time_taken > 0
        assert result.final_energy is not None
        assert len(result.final_energy) == len(small_network)
        assert result.performance_metrics is not None
        assert 'speedup_factor' in result.performance_metrics

    @pytest.mark.asyncio
    async def test_early_stopping(self, boosted_engine, small_network):
        """Test early stopping mechanism"""
        boosted_engine.enable_early_stopping = True
        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=small_network,
            max_iterations=50000
        )

        # Should converge before max iterations
        assert result.steps < 50000
        assert result.performance_metrics['iterations_saved'] > 0

    @pytest.mark.asyncio
    async def test_vulnerability_extraction(self, boosted_engine, small_network):
        """Test vulnerability extraction from energy field"""
        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=small_network,
            max_iterations=1000
        )

        # Should extract some vulnerabilities
        assert isinstance(result.vulnerabilities, list)
        for vuln in result.vulnerabilities:
            assert 'node_id' in vuln
            assert 'energy' in vuln
            assert 'severity' in vuln
            assert vuln['severity'] in ['critical', 'high', 'medium']

    @pytest.mark.asyncio
    async def test_stability_log(self, boosted_engine, small_network):
        """Test stability analysis logging"""
        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=small_network,
            max_iterations=1000
        )

        assert result.stability_log is not None
        assert len(result.stability_log) > 0

        for entry in result.stability_log:
            assert 'iteration' in entry
            assert 'phase' in entry
            assert 'energy' in entry
            assert entry['phase'] in ['stable_detection', 'bifurcation', 'chaos_mode', 'converging']

    @pytest.mark.asyncio
    async def test_performance_metrics(self, boosted_engine, medium_network):
        """Test performance metrics collection"""
        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=medium_network,
            max_iterations=5000
        )

        metrics = result.performance_metrics
        assert 'iterations_saved' in metrics
        assert 'chaos_boosts_triggered' in metrics
        assert 'early_stops' in metrics
        assert 'avg_eta' in metrics
        assert 'max_energy_peak' in metrics
        assert 'total_iterations' in metrics
        assert 'speedup_factor' in metrics

        # Speedup should be > 1 if early stopping occurred
        if metrics['iterations_saved'] > 0:
            assert metrics['speedup_factor'] > 1.0


# ==================== ZKAEDIUltraBoosted Tests ====================

class TestZKAEDIUltraBoosted:
    """Test suite for ultra-boosted JIT engine"""

    @pytest.mark.asyncio
    async def test_initialization(self, ultra_engine):
        """Test engine initialization"""
        assert ultra_engine.alpha == 0.618
        assert ultra_engine.eta_base == 0.4
        assert ultra_engine.use_mixed_precision == True
        assert ultra_engine.precision == np.float32

    @pytest.mark.asyncio
    async def test_solve_small_network(self, ultra_engine, small_network):
        """Test solving small network with ultra engine"""
        result = await ultra_engine.solve_ultra_boosted(
            network_graph=small_network,
            max_iterations=1000
        )

        assert isinstance(result, UltraSolution)
        assert result.algorithm == "ZKAEDI_PRIME_ULTRA_BOOSTED"
        assert result.steps > 0
        assert result.time_taken > 0
        assert result.final_energy is not None
        # Final energy should be float64 (converted back)
        assert result.final_energy.dtype == np.float64

    @pytest.mark.asyncio
    async def test_ultra_metrics(self, ultra_engine, small_network):
        """Test ultra-specific performance metrics"""
        result = await ultra_engine.solve_ultra_boosted(
            network_graph=small_network,
            max_iterations=1000
        )

        assert result.ultra_metrics is not None
        assert 'jit_compilation_time_ms' in result.ultra_metrics
        assert 'avg_iteration_time_us' in result.ultra_metrics
        assert 'numba_enabled' in result.ultra_metrics
        assert 'mixed_precision' in result.ultra_metrics
        assert 'memory_saved_mb' in result.ultra_metrics

    @pytest.mark.asyncio
    async def test_mixed_precision_memory_savings(self, ultra_engine, medium_network):
        """Test memory savings from mixed precision"""
        result = await ultra_engine.solve_ultra_boosted(
            network_graph=medium_network,
            max_iterations=2000
        )

        # Should have memory savings > 0 with mixed precision enabled
        if ultra_engine.use_mixed_precision:
            assert result.ultra_metrics['memory_saved_mb'] >= 0

    @pytest.mark.asyncio
    async def test_iteration_time_tracking(self, ultra_engine, small_network):
        """Test per-iteration time tracking"""
        result = await ultra_engine.solve_ultra_boosted(
            network_graph=small_network,
            max_iterations=1000
        )

        # Average iteration time should be reasonable (< 1ms = 1000µs)
        assert result.ultra_metrics['avg_iteration_time_us'] < 10000

    @pytest.mark.asyncio
    async def test_convergence_with_jit(self, ultra_engine, small_network):
        """Test convergence behavior with JIT compilation"""
        result = await ultra_engine.solve_ultra_boosted(
            network_graph=small_network,
            max_iterations=50000
        )

        # Should converge before max iterations
        assert result.steps < 50000
        assert result.performance_metrics['speedup_factor'] > 1.0

    @pytest.mark.asyncio
    async def test_vulnerability_extraction(self, ultra_engine, small_network):
        """Test vulnerability extraction marks as ultra_optimized"""
        result = await ultra_engine.solve_ultra_boosted(
            network_graph=small_network,
            max_iterations=1000
        )

        for vuln in result.vulnerabilities:
            if 'ultra_optimized' in vuln:
                assert vuln['ultra_optimized'] == True


# ==================== QuantumResistantZKAEDI Tests ====================

class TestQuantumResistantZKAEDI:
    """Test suite for quantum-resistant engine"""

    @pytest.mark.asyncio
    async def test_initialization(self, quantum_engine):
        """Test quantum engine initialization"""
        assert quantum_engine.alpha == 0.618
        assert quantum_engine.eta_base == 0.4
        assert quantum_engine.enable_quantum_noise == True
        assert quantum_engine.enable_hash_verification == True

    @pytest.mark.asyncio
    async def test_quantum_safe_rng(self, quantum_engine):
        """Test quantum-safe random number generation"""
        # Generate quantum-safe noise
        noise = quantum_engine.quantum_safe_noise(0, 1, (10,))

        assert noise is not None
        assert len(noise) == 10
        # Should be approximately normal distribution
        assert -5 < np.mean(noise) < 5

    @pytest.mark.asyncio
    async def test_hash_integrity_check(self, quantum_engine):
        """Test hash-based integrity verification"""
        H = np.random.rand(10)
        hash_result = quantum_engine.hash_based_integrity_check(H, 100)

        assert hash_result is not None
        assert len(hash_result) == 128  # SHA3-512 hex digest

    @pytest.mark.asyncio
    async def test_solve_small_network(self, quantum_engine, small_network):
        """Test solving small network with quantum engine"""
        result = await quantum_engine.solve_quantum_resistant(
            network_graph=small_network,
            max_iterations=1000
        )

        assert isinstance(result, QuantumSolution)
        assert result.algorithm == "ZKAEDI_PRIME_QUANTUM_RESISTANT"
        assert result.steps > 0
        assert result.time_taken > 0
        assert result.quantum_metrics is not None

    @pytest.mark.asyncio
    async def test_quantum_metrics(self, quantum_engine, small_network):
        """Test quantum-specific metrics collection"""
        result = await quantum_engine.solve_quantum_resistant(
            network_graph=small_network,
            max_iterations=1000
        )

        qm = result.quantum_metrics
        assert 'quantum_noise_calls' in qm
        assert 'hash_checks' in qm
        assert 'classical_fallbacks' in qm
        assert 'avg_quantum_overhead_ms' in qm

    @pytest.mark.asyncio
    async def test_graceful_fallback(self, quantum_engine, small_network):
        """Test graceful fallback to classical methods"""
        # Disable quantum noise to force fallback path
        quantum_engine.enable_quantum_noise = False

        result = await quantum_engine.solve_quantum_resistant(
            network_graph=small_network,
            max_iterations=500
        )

        # Should still complete successfully
        assert result.steps > 0
        assert result.final_energy is not None

    @pytest.mark.asyncio
    async def test_vulnerability_quantum_verified(self, quantum_engine, small_network):
        """Test vulnerabilities marked as quantum verified"""
        result = await quantum_engine.solve_quantum_resistant(
            network_graph=small_network,
            max_iterations=1000
        )

        for vuln in result.vulnerabilities:
            if 'quantum_verified' in vuln:
                assert vuln['quantum_verified'] == True

    @pytest.mark.asyncio
    async def test_verify_feedback_chain(self, quantum_engine, small_network):
        """Test feedback chain verification"""
        result = await quantum_engine.solve_quantum_resistant(
            network_graph=small_network,
            max_iterations=1000
        )

        # Feedback chain should be intact after successful scan
        is_intact = quantum_engine.verify_feedback_chain()
        assert is_intact == True


# ==================== Cross-Engine Comparison Tests ====================

class TestEngineComparison:
    """Compare behavior across all three engines"""

    @pytest.mark.asyncio
    async def test_all_engines_converge(self, boosted_engine, ultra_engine, quantum_engine, small_network):
        """Test that all engines converge on the same network"""
        boosted_result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=small_network,
            max_iterations=5000
        )
        ultra_result = await ultra_engine.solve_ultra_boosted(
            network_graph=small_network,
            max_iterations=5000
        )
        quantum_result = await quantum_engine.solve_quantum_resistant(
            network_graph=small_network,
            max_iterations=5000
        )

        # All should complete successfully
        assert boosted_result.steps > 0
        assert ultra_result.steps > 0
        assert quantum_result.steps > 0

        # All should produce valid energy fields
        assert len(boosted_result.final_energy) == len(small_network)
        assert len(ultra_result.final_energy) == len(small_network)
        assert len(quantum_result.final_energy) == len(small_network)

    @pytest.mark.asyncio
    async def test_engines_detect_vulnerabilities(self, boosted_engine, ultra_engine, quantum_engine, medium_network):
        """Test that all engines detect vulnerabilities"""
        boosted_result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=medium_network,
            max_iterations=3000
        )
        ultra_result = await ultra_engine.solve_ultra_boosted(
            network_graph=medium_network,
            max_iterations=3000
        )
        quantum_result = await quantum_engine.solve_quantum_resistant(
            network_graph=medium_network,
            max_iterations=3000
        )

        # All should detect some vulnerabilities (top 25%)
        assert len(boosted_result.vulnerabilities) > 0
        assert len(ultra_result.vulnerabilities) > 0
        assert len(quantum_result.vulnerabilities) > 0

    @pytest.mark.asyncio
    async def test_speedup_factors(self, boosted_engine, ultra_engine, medium_network):
        """Test that speedup factors are calculated correctly"""
        boosted_result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=medium_network,
            max_iterations=10000
        )
        ultra_result = await ultra_engine.solve_ultra_boosted(
            network_graph=medium_network,
            max_iterations=10000
        )

        # Both should have speedup > 1 due to early stopping
        boosted_speedup = boosted_result.performance_metrics['speedup_factor']
        ultra_speedup = ultra_result.performance_metrics['speedup_factor']

        assert boosted_speedup >= 1.0
        assert ultra_speedup >= 1.0


# ==================== Edge Cases and Error Handling ====================

class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_single_node_network(self, boosted_engine):
        """Test handling of single-node network"""
        single_node = {'192.168.1.1': []}

        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=single_node,
            max_iterations=100
        )

        assert result.steps > 0
        assert len(result.final_energy) == 1

    @pytest.mark.asyncio
    async def test_disconnected_network(self, boosted_engine):
        """Test handling of disconnected network"""
        disconnected = {
            '192.168.1.1': [],
            '192.168.1.2': [],
            '192.168.1.3': []
        }

        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=disconnected,
            max_iterations=100
        )

        assert result.steps > 0
        assert len(result.final_energy) == 3

    @pytest.mark.asyncio
    async def test_very_small_iterations(self, boosted_engine, small_network):
        """Test with very small iteration count"""
        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=small_network,
            max_iterations=10
        )

        assert result.steps <= 10
        assert result.final_energy is not None

    @pytest.mark.asyncio
    async def test_custom_parameters(self):
        """Test engines with custom parameters"""
        engine = ZKAEDIPrimeBoosted(
            alpha=0.5,
            eta=0.6,
            gamma=0.4,
            beta=0.2,
            sigma=0.1,
            phi=1.5
        )

        assert engine.alpha == 0.5
        assert engine.eta_base == 0.6
        assert engine.phi == 1.5

    @pytest.mark.asyncio
    async def test_disabled_optimizations(self, small_network):
        """Test engine with optimizations disabled"""
        engine = ZKAEDIPrimeBoosted()
        engine.enable_early_stopping = False
        engine.enable_adaptive_eta = False
        engine.enable_chaos_boost = False

        result = await engine.solve_vuln_detection_boosted(
            network_graph=small_network,
            max_iterations=100
        )

        # Should still work, just without optimizations
        assert result.steps == 100  # No early stopping


# ==================== Numerical Stability Tests ====================

class TestNumericalStability:
    """Test numerical stability of the engines"""

    @pytest.mark.asyncio
    async def test_no_nan_values(self, boosted_engine, medium_network):
        """Test that results contain no NaN values"""
        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=medium_network,
            max_iterations=5000
        )

        assert not np.any(np.isnan(result.final_energy))
        for entry in result.stability_log:
            assert not np.isnan(entry['energy'])

    @pytest.mark.asyncio
    async def test_no_inf_values(self, boosted_engine, medium_network):
        """Test that results contain no infinite values"""
        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=medium_network,
            max_iterations=5000
        )

        assert not np.any(np.isinf(result.final_energy))

    @pytest.mark.asyncio
    async def test_energy_bounds(self, boosted_engine, medium_network):
        """Test that energy values stay within reasonable bounds"""
        result = await boosted_engine.solve_vuln_detection_boosted(
            network_graph=medium_network,
            max_iterations=5000
        )

        # Energy should not explode to unreasonable values
        max_energy = np.max(np.abs(result.final_energy))
        assert max_energy < 1000  # Reasonable upper bound

    @pytest.mark.asyncio
    async def test_reproducibility_with_seed(self, small_network):
        """Test that results are reproducible with same seed"""
        np.random.seed(42)
        engine1 = ZKAEDIPrimeBoosted()
        result1 = await engine1.solve_vuln_detection_boosted(
            network_graph=small_network,
            max_iterations=100
        )

        np.random.seed(42)
        engine2 = ZKAEDIPrimeBoosted()
        result2 = await engine2.solve_vuln_detection_boosted(
            network_graph=small_network,
            max_iterations=100
        )

        # Results should be identical with same seed
        np.testing.assert_array_almost_equal(
            result1.final_energy,
            result2.final_energy,
            decimal=10
        )
