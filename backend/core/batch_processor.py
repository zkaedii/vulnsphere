"""
Batch Processing for Multiple Networks

Provides efficient batch scanning of multiple networks with:
- Parallel execution using asyncio
- Shared JIT compilation cache
- Progress tracking
- Result aggregation
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import time
import logging

from backend.core.zkaedi_prime_boosted import ZKAEDIPrimeBoosted, EnhancedSolution
from backend.core.zkaedi_ultra_boosted import ZKAEDIUltraBoosted, UltraSolution
from backend.core.quantum_resistant_engine import QuantumResistantZKAEDI, QuantumSolution
from backend.core.sparse_hamiltonian import SparseHamiltonianEngine, SparseHamiltonianResult

logger = logging.getLogger(__name__)


@dataclass
class BatchProgress:
    """Track progress of batch processing"""
    batch_id: str
    total: int
    completed: int = 0
    failed: int = 0
    in_progress: int = 0
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None

    @property
    def progress_pct(self) -> float:
        return (self.completed + self.failed) / self.total * 100 if self.total > 0 else 0

    @property
    def elapsed_seconds(self) -> float:
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()

    def to_dict(self) -> Dict:
        return {
            'batch_id': self.batch_id,
            'total': self.total,
            'completed': self.completed,
            'failed': self.failed,
            'in_progress': self.in_progress,
            'progress_pct': self.progress_pct,
            'elapsed_seconds': self.elapsed_seconds
        }


@dataclass
class BatchResult:
    """Result from batch processing"""
    batch_id: str
    total_networks: int
    successful: int
    failed: int
    total_time: float
    avg_time_per_network: float
    results: List[Dict]
    errors: List[Dict]
    summary: Dict


class BatchProcessor:
    """
    Process multiple networks in batch with configurable parallelism.

    Supports all engine types:
    - boosted: ZKAEDIPrimeBoosted
    - ultra: ZKAEDIUltraBoosted
    - quantum: QuantumResistantZKAEDI
    - sparse: SparseHamiltonianEngine
    """

    def __init__(
        self,
        engine_type: str = "boosted",
        max_concurrency: int = 4,
        **engine_kwargs
    ):
        """
        Initialize batch processor.

        Args:
            engine_type: Type of engine to use
            max_concurrency: Maximum parallel scans
            **engine_kwargs: Parameters passed to engine constructor
        """
        self.engine_type = engine_type
        self.max_concurrency = max_concurrency
        self.engine_kwargs = engine_kwargs or {
            'alpha': 0.618,
            'eta': 0.4,
            'gamma': 0.3,
            'beta': 0.1,
            'sigma': 0.05
        }

        # Progress tracking
        self._active_batches: Dict[str, BatchProgress] = {}
        self._progress_callbacks: List[Callable] = []

        # Engine pool for reuse (saves JIT compilation time for ultra)
        self._engine_pool: List[Any] = []
        self._pool_lock = asyncio.Lock()

        logger.info(f"BatchProcessor initialized: engine={engine_type}, concurrency={max_concurrency}")

    def _create_engine(self):
        """Create engine instance based on type"""
        if self.engine_type == "boosted":
            return ZKAEDIPrimeBoosted(**self.engine_kwargs)
        elif self.engine_type == "ultra":
            return ZKAEDIUltraBoosted(**self.engine_kwargs)
        elif self.engine_type == "quantum":
            return QuantumResistantZKAEDI(**{k: v for k, v in self.engine_kwargs.items() if k in ['alpha', 'eta']})
        elif self.engine_type == "sparse":
            return SparseHamiltonianEngine(**self.engine_kwargs)
        else:
            raise ValueError(f"Unknown engine type: {self.engine_type}")

    async def _get_engine(self):
        """Get engine from pool or create new one"""
        async with self._pool_lock:
            if self._engine_pool:
                return self._engine_pool.pop()
            return self._create_engine()

    async def _return_engine(self, engine):
        """Return engine to pool for reuse"""
        async with self._pool_lock:
            if len(self._engine_pool) < self.max_concurrency:
                self._engine_pool.append(engine)

    async def _scan_single(
        self,
        network_id: str,
        network_graph: Dict[str, List[str]],
        max_iterations: int
    ) -> Dict:
        """Scan a single network"""
        engine = await self._get_engine()

        try:
            start = time.perf_counter()

            # Run scan based on engine type
            if self.engine_type == "boosted":
                result = await engine.solve_vuln_detection_boosted(
                    network_graph=network_graph,
                    max_iterations=max_iterations
                )
            elif self.engine_type == "ultra":
                result = await engine.solve_ultra_boosted(
                    network_graph=network_graph,
                    max_iterations=max_iterations
                )
            elif self.engine_type == "quantum":
                result = await engine.solve_quantum_resistant(
                    network_graph=network_graph,
                    max_iterations=max_iterations
                )
            elif self.engine_type == "sparse":
                result = await engine.solve_sparse(
                    network_graph=network_graph,
                    max_iterations=max_iterations
                )

            elapsed = time.perf_counter() - start

            return {
                'network_id': network_id,
                'status': 'success',
                'time_taken': elapsed,
                'iterations': result.steps,
                'converged': result.converged,
                'vulnerabilities_count': len(result.vulnerabilities),
                'vulnerabilities': result.vulnerabilities[:20],  # Limit for memory
                'performance_metrics': result.performance_metrics,
                'error': None
            }

        except Exception as e:
            logger.error(f"Scan failed for {network_id}: {e}")
            return {
                'network_id': network_id,
                'status': 'failed',
                'time_taken': 0,
                'iterations': 0,
                'converged': False,
                'vulnerabilities_count': 0,
                'vulnerabilities': [],
                'performance_metrics': {},
                'error': str(e)
            }

        finally:
            await self._return_engine(engine)

    def add_progress_callback(self, callback: Callable[[BatchProgress], None]):
        """Add callback for progress updates"""
        self._progress_callbacks.append(callback)

    def _update_progress(self, batch_id: str, completed: bool, failed: bool):
        """Update progress and notify callbacks"""
        if batch_id not in self._active_batches:
            return

        progress = self._active_batches[batch_id]
        progress.in_progress -= 1

        if completed:
            progress.completed += 1
        if failed:
            progress.failed += 1

        # Notify callbacks
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    async def process_batch(
        self,
        networks: List[Dict[str, Any]],
        max_iterations: int = 50000
    ) -> BatchResult:
        """
        Process batch of networks.

        Args:
            networks: List of dicts with 'id' and 'graph' keys
            max_iterations: Max iterations per scan

        Returns:
            BatchResult with all scan results
        """
        batch_id = str(uuid.uuid4())[:8]
        total = len(networks)

        logger.info(f"Starting batch {batch_id}: {total} networks")

        # Initialize progress tracking
        progress = BatchProgress(
            batch_id=batch_id,
            total=total
        )
        self._active_batches[batch_id] = progress

        start_time = time.perf_counter()

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def scan_with_semaphore(network_info: Dict) -> Dict:
            async with semaphore:
                progress.in_progress += 1
                network_id = network_info.get('id', str(uuid.uuid4())[:8])
                network_graph = network_info.get('graph', network_info)

                result = await self._scan_single(
                    network_id=network_id,
                    network_graph=network_graph,
                    max_iterations=max_iterations
                )

                self._update_progress(
                    batch_id,
                    completed=result['status'] == 'success',
                    failed=result['status'] == 'failed'
                )

                return result

        # Run all scans concurrently (limited by semaphore)
        results = await asyncio.gather(*[
            scan_with_semaphore(net) for net in networks
        ])

        total_time = time.perf_counter() - start_time

        # Update progress
        progress.end_time = datetime.utcnow()

        # Separate successful and failed
        successful_results = [r for r in results if r['status'] == 'success']
        failed_results = [r for r in results if r['status'] == 'failed']

        # Calculate summary statistics
        summary = self._calculate_summary(successful_results)

        # Cleanup
        del self._active_batches[batch_id]

        logger.info(f"Batch {batch_id} complete: {len(successful_results)}/{total} successful in {total_time:.2f}s")

        return BatchResult(
            batch_id=batch_id,
            total_networks=total,
            successful=len(successful_results),
            failed=len(failed_results),
            total_time=total_time,
            avg_time_per_network=total_time / total if total > 0 else 0,
            results=successful_results,
            errors=failed_results,
            summary=summary
        )

    def _calculate_summary(self, results: List[Dict]) -> Dict:
        """Calculate summary statistics from results"""
        if not results:
            return {
                'total_vulnerabilities': 0,
                'avg_vulnerabilities': 0,
                'avg_time': 0,
                'avg_iterations': 0,
                'convergence_rate': 0,
                'severity_breakdown': {}
            }

        total_vulns = sum(r['vulnerabilities_count'] for r in results)
        times = [r['time_taken'] for r in results]
        iterations = [r['iterations'] for r in results]
        converged = sum(1 for r in results if r['converged'])

        # Aggregate severity breakdown
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for result in results:
            for vuln in result['vulnerabilities']:
                sev = vuln.get('severity', 'medium').lower()
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            'total_vulnerabilities': total_vulns,
            'avg_vulnerabilities': total_vulns / len(results),
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'avg_iterations': sum(iterations) / len(iterations),
            'convergence_rate': converged / len(results),
            'severity_breakdown': severity_counts
        }

    def get_batch_progress(self, batch_id: str) -> Optional[BatchProgress]:
        """Get progress for active batch"""
        return self._active_batches.get(batch_id)

    def list_active_batches(self) -> List[Dict]:
        """List all active batches"""
        return [p.to_dict() for p in self._active_batches.values()]


async def example_batch_processing():
    """Example batch processing"""
    print("=" * 60)
    print("VulnSphere PRIME - Batch Processing Example")
    print("=" * 60)

    # Create test networks
    networks = []
    for i in range(5):
        n_nodes = 50 + i * 20
        network = {}
        for j in range(n_nodes):
            node_id = f"network_{i}_node_{j}"
            n_conn = min(5, n_nodes - 1)
            neighbors = [f"network_{i}_node_{k}" for k in range(n_conn) if k != j]
            network[node_id] = neighbors
        networks.append({'id': f'network_{i}', 'graph': network})

    print(f"\nProcessing {len(networks)} networks...")

    # Create processor
    processor = BatchProcessor(
        engine_type="boosted",
        max_concurrency=3
    )

    # Add progress callback
    def on_progress(progress: BatchProgress):
        print(f"  Progress: {progress.completed}/{progress.total} ({progress.progress_pct:.1f}%)")

    processor.add_progress_callback(on_progress)

    # Process batch
    result = await processor.process_batch(
        networks=networks,
        max_iterations=5000
    )

    print(f"\n" + "=" * 40)
    print("Results:")
    print(f"  Total time: {result.total_time:.2f}s")
    print(f"  Successful: {result.successful}/{result.total_networks}")
    print(f"  Failed: {result.failed}")
    print(f"  Avg time/network: {result.avg_time_per_network:.2f}s")
    print(f"\nSummary:")
    print(f"  Total vulnerabilities: {result.summary['total_vulnerabilities']}")
    print(f"  Avg vulnerabilities: {result.summary['avg_vulnerabilities']:.1f}")
    print(f"  Convergence rate: {result.summary['convergence_rate']*100:.1f}%")
    print(f"  Severity: {result.summary['severity_breakdown']}")


if __name__ == "__main__":
    asyncio.run(example_batch_processing())
