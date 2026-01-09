"""
MPI Distributed Hamiltonian Evolution

Implements domain decomposition for large-scale network analysis
across multiple compute nodes using MPI.

Requirements:
- mpi4py (pip install mpi4py)
- MPI runtime (OpenMPI, MPICH)

Usage:
    mpiexec -n 4 python -m backend.core.mpi_hamiltonian
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

# Try to import MPI
try:
    from mpi4py import MPI
    MPI_AVAILABLE = True
except ImportError:
    MPI_AVAILABLE = False
    MPI = None
    logger.warning("mpi4py not available - MPI features disabled")


@dataclass
class MPIConfig:
    """MPI configuration"""
    comm: Any  # MPI.Comm
    rank: int
    size: int
    root: int = 0


@dataclass
class DistributedResult:
    """Result from distributed computation"""
    energy_field: np.ndarray
    steps: int
    time_taken: float
    converged: bool
    local_chunk_size: int
    communication_time: float
    computation_time: float
    vulnerabilities: List[Dict]
    performance_metrics: Dict


class MPIHamiltonianEngine:
    """
    MPI-parallelized Hamiltonian evolution for large networks.

    Uses 1D domain decomposition: each rank handles a subset of nodes.
    Halo exchange synchronizes boundary information.
    """

    def __init__(
        self,
        alpha: float = 0.618,
        eta: float = 0.4,
        gamma: float = 0.3,
        beta: float = 0.1,
        sigma: float = 0.05
    ):
        self.alpha = alpha
        self.eta_base = eta
        self.gamma = gamma
        self.beta = beta
        self.sigma = sigma

        # MPI setup
        if MPI_AVAILABLE:
            self.comm = MPI.COMM_WORLD
            self.rank = self.comm.Get_rank()
            self.size = self.comm.Get_size()
        else:
            self.comm = None
            self.rank = 0
            self.size = 1

        self.is_root = self.rank == 0

        if self.is_root:
            logger.info(f"MPI Hamiltonian Engine: {self.size} processes")

    def decompose_domain(
        self,
        network_graph: Dict[str, List[str]]
    ) -> Tuple[Dict[str, List[str]], List[int], List[int]]:
        """
        Decompose network into chunks for each MPI rank.

        Returns:
            - Local subgraph for this rank
            - Chunk sizes for all ranks
            - Chunk offsets for all ranks
        """
        nodes = list(network_graph.keys())
        n_total = len(nodes)

        # Calculate chunk sizes (approximately equal)
        base_chunk = n_total // self.size
        remainder = n_total % self.size

        chunk_sizes = []
        offsets = []
        current_offset = 0

        for r in range(self.size):
            # Distribute remainder across first 'remainder' ranks
            chunk = base_chunk + (1 if r < remainder else 0)
            chunk_sizes.append(chunk)
            offsets.append(current_offset)
            current_offset += chunk

        # Extract local nodes
        local_start = offsets[self.rank]
        local_end = local_start + chunk_sizes[self.rank]
        local_nodes = nodes[local_start:local_end]

        # Build local subgraph
        local_graph = {}
        for node in local_nodes:
            local_graph[node] = network_graph.get(node, [])

        return local_graph, chunk_sizes, offsets

    def halo_exchange(
        self,
        local_H: np.ndarray,
        chunk_sizes: List[int],
        offsets: List[int]
    ) -> np.ndarray:
        """
        Exchange boundary values with neighboring ranks.

        Uses non-blocking sends/receives for overlap.
        """
        if not MPI_AVAILABLE or self.size == 1:
            return local_H

        # Determine neighbors
        left_rank = self.rank - 1 if self.rank > 0 else MPI.PROC_NULL
        right_rank = self.rank + 1 if self.rank < self.size - 1 else MPI.PROC_NULL

        # Halo width (number of boundary elements to exchange)
        halo_width = min(10, len(local_H) // 2) if len(local_H) > 1 else 0

        if halo_width == 0:
            return local_H

        # Prepare send buffers (boundary values)
        send_left = local_H[:halo_width].copy()
        send_right = local_H[-halo_width:].copy()

        # Prepare receive buffers
        recv_left = np.zeros(halo_width)
        recv_right = np.zeros(halo_width)

        # Non-blocking exchange
        requests = []

        # Send to left, receive from right
        if left_rank != MPI.PROC_NULL:
            requests.append(self.comm.Isend(send_left, dest=left_rank, tag=0))
        if right_rank != MPI.PROC_NULL:
            requests.append(self.comm.Irecv(recv_right, source=right_rank, tag=0))

        # Send to right, receive from left
        if right_rank != MPI.PROC_NULL:
            requests.append(self.comm.Isend(send_right, dest=right_rank, tag=1))
        if left_rank != MPI.PROC_NULL:
            requests.append(self.comm.Irecv(recv_left, source=left_rank, tag=1))

        # Wait for all exchanges
        MPI.Request.Waitall(requests)

        # Apply received halo values (blend with local boundary)
        if left_rank != MPI.PROC_NULL:
            local_H[:halo_width] = 0.5 * local_H[:halo_width] + 0.5 * recv_left
        if right_rank != MPI.PROC_NULL:
            local_H[-halo_width:] = 0.5 * local_H[-halo_width:] + 0.5 * recv_right

        return local_H

    def adaptive_eta_decay(self, t: int, base_eta: float) -> float:
        """Adaptive η cooling schedule"""
        decay_rate = 0.92
        decay_interval = 8000
        current_eta = base_eta * (decay_rate ** (t / decay_interval))
        return max(current_eta, base_eta * 0.3)

    def chaos_boost_eta(self, H: np.ndarray, current_eta: float) -> float:
        """Chaos boost for high energy"""
        max_energy = np.max(np.abs(H))
        if max_energy > 9.5:
            return min(0.82, current_eta + 0.18)
        return current_eta

    async def solve_distributed(
        self,
        network_graph: Dict[str, List[str]],
        max_iterations: int = 50000
    ) -> DistributedResult:
        """
        Distributed Hamiltonian evolution using MPI.

        Each rank evolves its local domain and exchanges
        boundary information with neighbors.
        """
        start_time = time.perf_counter()
        comm_time = 0.0
        comp_time = 0.0

        # Domain decomposition
        local_graph, chunk_sizes, offsets = self.decompose_domain(network_graph)
        local_n = len(local_graph)

        if self.is_root:
            logger.info(f"Domain decomposition: {chunk_sizes} nodes per rank")

        # Initialize local energy field
        local_H = np.random.rand(local_n).astype(np.float32) * 0.1
        local_H_base = local_H.copy()
        local_H_prev = local_H.copy()

        local_history = [local_H.copy()]

        performance_metrics = {
            'chaos_boosts': 0,
            'iterations_run': 0,
            'max_energy': 0
        }

        converged = False

        for t in range(max_iterations):
            comp_start = time.perf_counter()

            # Adaptive eta
            current_eta = self.adaptive_eta_decay(t, self.eta_base)
            current_eta = self.chaos_boost_eta(local_H, current_eta)

            if current_eta > self.eta_base + 0.1:
                performance_metrics['chaos_boosts'] += 1

            # Local Hamiltonian evolution
            sigmoid = 1.0 / (1.0 + np.exp(-self.gamma * local_H))
            noise = np.random.normal(0, 1 + self.beta * np.abs(local_H), size=local_H.shape).astype(np.float32)

            # Fractal derivative
            h = self.sigma
            t_scaled = t * h
            delta_psi = (t_scaled + h) ** self.alpha - t_scaled ** self.alpha if t_scaled > 0 else h ** self.alpha
            if abs(delta_psi) < 1e-10:
                delta_psi = 1e-10

            fractal_deriv = (local_H - local_H_prev) / delta_psi
            local_H_new = local_H_base + current_eta * fractal_deriv * sigmoid + self.sigma * noise

            comp_time += time.perf_counter() - comp_start

            # Halo exchange
            comm_start = time.perf_counter()
            local_H_new = self.halo_exchange(local_H_new, chunk_sizes, offsets)
            comm_time += time.perf_counter() - comm_start

            local_H_prev = local_H.copy()
            local_H = local_H_new
            local_history.append(local_H.copy())

            # Track max energy
            local_max = np.max(np.abs(local_H))
            if local_max > performance_metrics['max_energy']:
                performance_metrics['max_energy'] = float(local_max)

            # Check convergence (every 100 iterations)
            if t % 100 == 0 and t > 1500 and len(local_history) > 150:
                current_max = np.max(np.abs(local_H))
                past_max = np.max(np.abs(local_history[-150]))
                local_converged = abs(current_max - past_max) < 0.008

                # Global convergence check (all ranks must agree)
                if MPI_AVAILABLE and self.size > 1:
                    all_converged = self.comm.allreduce(local_converged, op=MPI.LAND)
                else:
                    all_converged = local_converged

                if all_converged:
                    if self.is_root:
                        logger.info(f"Global convergence at t={t}")
                    converged = True
                    break

            # Limit history
            if len(local_history) > 200:
                local_history = local_history[-200:]

            await asyncio.sleep(0.0001)

        performance_metrics['iterations_run'] = t + 1

        # Gather results to root
        if MPI_AVAILABLE and self.size > 1:
            # Gather all local energy fields
            sendbuf = local_H.astype(np.float64)
            recvbuf = None

            if self.is_root:
                recvbuf = np.empty(sum(chunk_sizes), dtype=np.float64)

            # Use Gatherv for variable chunk sizes
            self.comm.Gatherv(
                sendbuf,
                [recvbuf, chunk_sizes, offsets, MPI.DOUBLE] if self.is_root else None,
                root=0
            )

            global_H = recvbuf if self.is_root else local_H.astype(np.float64)
        else:
            global_H = local_H.astype(np.float64)

        elapsed = time.perf_counter() - start_time

        # Extract vulnerabilities (root only)
        vulnerabilities = []
        if self.is_root:
            vulnerabilities = self._extract_vulnerabilities(global_H, network_graph)

        return DistributedResult(
            energy_field=global_H,
            steps=t + 1,
            time_taken=elapsed,
            converged=converged,
            local_chunk_size=local_n,
            communication_time=comm_time,
            computation_time=comp_time,
            vulnerabilities=vulnerabilities,
            performance_metrics=performance_metrics
        )

    def _extract_vulnerabilities(
        self,
        H: np.ndarray,
        network_graph: Dict[str, List[str]]
    ) -> List[Dict]:
        """Extract vulnerabilities from global energy field"""
        threshold = np.percentile(H, 75)
        vulns = []

        nodes = list(network_graph.keys())
        for i, node_id in enumerate(nodes):
            if i < len(H) and H[i] > threshold:
                vulns.append({
                    'node_id': node_id,
                    'energy': float(H[i]),
                    'severity': 'critical' if H[i] > 8 else 'high' if H[i] > 5 else 'medium',
                    'neighbors': network_graph.get(node_id, []),
                    'risk_score': min(100, int(H[i] * 10)),
                    'mpi_distributed': True
                })

        return sorted(vulns, key=lambda x: x['energy'], reverse=True)


def run_mpi_benchmark():
    """Run MPI benchmark (execute with mpiexec)"""
    if not MPI_AVAILABLE:
        print("MPI not available. Install mpi4py and run with mpiexec.")
        return

    engine = MPIHamiltonianEngine()

    # Create test network
    n_nodes = 1000
    network = {}
    for i in range(n_nodes):
        node_id = f"node_{i}"
        # Random connections (sparse)
        n_connections = np.random.randint(1, 10)
        neighbors = [f"node_{np.random.randint(0, n_nodes)}" for _ in range(n_connections)]
        network[node_id] = neighbors

    if engine.is_root:
        print(f"Running MPI benchmark with {n_nodes} nodes across {engine.size} processes")

    # Run distributed solve
    result = asyncio.run(engine.solve_distributed(network, max_iterations=5000))

    if engine.is_root:
        print(f"\nResults:")
        print(f"  Time: {result.time_taken:.2f}s")
        print(f"  Iterations: {result.steps}")
        print(f"  Converged: {result.converged}")
        print(f"  Communication time: {result.communication_time:.3f}s")
        print(f"  Computation time: {result.computation_time:.3f}s")
        print(f"  Comm/Total: {result.communication_time/result.time_taken*100:.1f}%")
        print(f"  Vulnerabilities: {len(result.vulnerabilities)}")


if __name__ == "__main__":
    run_mpi_benchmark()
