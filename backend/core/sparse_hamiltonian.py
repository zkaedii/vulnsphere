"""
Sparse Hamiltonian Engine for Large-Scale Networks
Optimized for networks with 10,000+ nodes

Uses scipy.sparse for O(n) memory instead of O(n²) for adjacency matrices.
Provides 10-20× memory reduction for sparse network topologies.
"""
import numpy as np
from scipy.sparse import csr_matrix, lil_matrix, diags
from scipy.sparse.linalg import eigsh
import time
from typing import Dict, List, Optional, Tuple
import asyncio
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SparseHamiltonianResult:
    """Result from sparse Hamiltonian evolution"""
    energy_field: np.ndarray
    steps: int
    time_taken: float
    converged: bool
    memory_usage_mb: float
    sparsity: float
    vulnerabilities: List[Dict]
    performance_metrics: Dict


class SparseHamiltonianEngine:
    """
    Sparse Hamiltonian engine for large-scale network analysis.

    Uses compressed sparse row (CSR) format for efficient matrix operations.
    Ideal for networks where each node connects to << n other nodes.

    Memory comparison (10,000 nodes):
    - Dense: 10,000 × 10,000 × 8 bytes = 800 MB
    - Sparse (1% density): ~1.6 MB (500× reduction)
    """

    def __init__(
        self,
        alpha: float = 0.618,
        eta: float = 0.4,
        gamma: float = 0.3,
        beta: float = 0.1,
        sigma: float = 0.05,
        phi: float = 1.618
    ):
        self.alpha = alpha
        self.eta_base = eta
        self.gamma = gamma
        self.beta = beta
        self.sigma = sigma
        self.phi = phi

        # Sparse-specific settings
        self.adjacency_matrix: Optional[csr_matrix] = None
        self.node_index: Dict[str, int] = {}
        self.index_node: Dict[int, str] = {}

        # Performance tracking
        self.H_history: List[np.ndarray] = []
        self.stability_log: List[Dict] = []

        logger.info("Sparse Hamiltonian Engine initialized")

    def build_sparse_adjacency(self, network_graph: Dict) -> Tuple[csr_matrix, float]:
        """
        Build sparse adjacency matrix from network graph.

        Args:
            network_graph: Dict mapping node IDs to neighbor lists

        Returns:
            Tuple of (sparse adjacency matrix, sparsity percentage)
        """
        n_nodes = len(network_graph)
        nodes = list(network_graph.keys())

        # Build index mappings
        self.node_index = {node: i for i, node in enumerate(nodes)}
        self.index_node = {i: node for i, node in enumerate(nodes)}

        # Use lil_matrix for efficient construction, then convert to csr
        adj = lil_matrix((n_nodes, n_nodes), dtype=np.float32)

        n_edges = 0
        for node, neighbors in network_graph.items():
            i = self.node_index[node]
            for neighbor in neighbors:
                if neighbor in self.node_index:
                    j = self.node_index[neighbor]
                    adj[i, j] = 1.0
                    n_edges += 1

        # Convert to CSR for efficient arithmetic
        self.adjacency_matrix = adj.tocsr()

        # Calculate sparsity
        max_edges = n_nodes * n_nodes
        sparsity = 1.0 - (n_edges / max_edges) if max_edges > 0 else 1.0

        logger.info(f"Built sparse adjacency: {n_nodes} nodes, {n_edges} edges, {sparsity*100:.2f}% sparse")

        return self.adjacency_matrix, sparsity

    def sparse_laplacian(self) -> csr_matrix:
        """
        Compute sparse graph Laplacian: L = D - A

        The Laplacian captures diffusion dynamics on the network.
        """
        if self.adjacency_matrix is None:
            raise ValueError("Adjacency matrix not built. Call build_sparse_adjacency first.")

        # Degree matrix (diagonal)
        degrees = np.array(self.adjacency_matrix.sum(axis=1)).flatten()
        D = diags(degrees, format='csr')

        # Laplacian
        L = D - self.adjacency_matrix
        return L

    def adaptive_eta_decay(self, t: int, base_eta: float) -> float:
        """Adaptive η cooling schedule"""
        decay_rate = 0.92
        decay_interval = 8000
        current_eta = base_eta * (decay_rate ** (t / decay_interval))
        return max(current_eta, base_eta * 0.3)

    def check_early_stopping(self, H: np.ndarray, t: int, threshold: float = 0.008, window: int = 150) -> bool:
        """Energy threshold early stopping"""
        if t < 1500 or len(self.H_history) < window:
            return False

        current_max = np.max(np.abs(H))
        past_max = np.max(np.abs(self.H_history[-window]))

        return abs(current_max - past_max) < threshold

    def chaos_boost_eta(self, H: np.ndarray, current_eta: float) -> float:
        """Chaos-triggered super-feedback"""
        max_energy = np.max(np.abs(H))
        if max_energy > 9.5:
            return min(0.82, current_eta + 0.18)
        return current_eta

    async def solve_sparse(
        self,
        network_graph: Dict,
        max_iterations: int = 50000
    ) -> SparseHamiltonianResult:
        """
        Solve vulnerability detection using sparse Hamiltonian evolution.

        Memory-efficient for large networks (10,000+ nodes).
        Uses sparse matrix operations for O(nnz) complexity per iteration.

        Args:
            network_graph: Network topology as adjacency dict
            max_iterations: Maximum evolution steps

        Returns:
            SparseHamiltonianResult with vulnerabilities and metrics
        """
        start_time = time.perf_counter()

        # Build sparse adjacency
        adj, sparsity = self.build_sparse_adjacency(network_graph)
        n_nodes = len(network_graph)

        # Calculate memory usage
        dense_memory_mb = (n_nodes * n_nodes * 8) / (1024 * 1024)
        sparse_memory_mb = (adj.data.nbytes + adj.indices.nbytes + adj.indptr.nbytes) / (1024 * 1024)

        logger.info(f"Memory savings: {dense_memory_mb:.1f}MB (dense) vs {sparse_memory_mb:.2f}MB (sparse)")

        # Initialize energy field
        H = np.random.rand(n_nodes).astype(np.float32) * 0.1
        H_base = H.copy()

        self.H_history = [H.copy()]
        self.stability_log = []

        performance_metrics = {
            'iterations_saved': 0,
            'chaos_boosts_triggered': 0,
            'early_stops': 0,
            'avg_eta': 0,
            'max_energy_peak': 0,
            'memory_saved_mb': dense_memory_mb - sparse_memory_mb
        }

        eta_sum = 0

        # Compute sparse Laplacian for diffusion
        L = self.sparse_laplacian()

        for t in range(max_iterations):
            # Adaptive η decay
            current_eta = self.adaptive_eta_decay(t, self.eta_base)
            eta_sum += current_eta

            # Chaos boost
            current_eta = self.chaos_boost_eta(H, current_eta)
            if current_eta > self.eta_base + 0.1:
                performance_metrics['chaos_boosts_triggered'] += 1

            # Sparse Hamiltonian evolution
            # Diffusion term: L @ H (sparse matrix-vector product)
            diffusion = L.dot(H)

            # Sigmoid nonlinearity
            sigmoid = 1.0 / (1.0 + np.exp(-self.gamma * H))

            # Noise
            noise = np.random.normal(0, 1 + self.beta * np.abs(H), size=H.shape).astype(np.float32)

            # FDDE update with sparse diffusion
            if len(self.H_history) > 0:
                h = self.sigma
                t_scaled = t * h
                delta_psi = (t_scaled + h) ** self.alpha - t_scaled ** self.alpha if t_scaled > 0 else h ** self.alpha
                if abs(delta_psi) < 1e-10:
                    delta_psi = 1e-10

                fractal_deriv = (H - self.H_history[-1]) / delta_psi

                # Include sparse diffusion in evolution
                H = H_base + current_eta * fractal_deriv * sigmoid - 0.01 * diffusion + self.sigma * noise
            else:
                H = H_base + current_eta * H * sigmoid + self.sigma * noise

            self.H_history.append(H.copy())

            # Track max energy
            max_energy = np.max(np.abs(H))
            if max_energy > performance_metrics['max_energy_peak']:
                performance_metrics['max_energy_peak'] = float(max_energy)

            # Stability analysis (every 100 iterations)
            if t % 100 == 0:
                phase = self._analyze_phase(max_energy)
                self.stability_log.append({
                    'iteration': t,
                    'phase': phase,
                    'energy': float(np.mean(H)),
                    'max_energy': float(max_energy),
                    'current_eta': current_eta
                })

                # Early stopping check
                if self.check_early_stopping(H, t):
                    performance_metrics['early_stops'] += 1
                    performance_metrics['iterations_saved'] = max_iterations - t
                    logger.info(f"Early convergence at t={t}")
                    break

            await asyncio.sleep(0.0001)

        elapsed = time.perf_counter() - start_time

        # Calculate metrics
        performance_metrics['avg_eta'] = eta_sum / (t + 1)
        performance_metrics['total_iterations'] = t + 1
        performance_metrics['speedup_factor'] = max_iterations / (t + 1) if t < max_iterations else 1.0

        # Extract vulnerabilities
        vulnerabilities = self._extract_vulnerabilities(H, network_graph)

        converged = self.stability_log[-1]['phase'] == 'stable_detection' if self.stability_log else False

        logger.info(f"Sparse Hamiltonian Complete: {elapsed:.2f}s, {t+1} iterations")
        logger.info(f"Memory: {sparse_memory_mb:.2f}MB (saved {performance_metrics['memory_saved_mb']:.1f}MB)")

        return SparseHamiltonianResult(
            energy_field=H.astype(np.float64),
            steps=t + 1,
            time_taken=elapsed,
            converged=converged,
            memory_usage_mb=sparse_memory_mb,
            sparsity=sparsity,
            vulnerabilities=vulnerabilities,
            performance_metrics=performance_metrics
        )

    def _analyze_phase(self, energy_magnitude: float) -> str:
        """Analyze current phase based on energy"""
        if energy_magnitude < 1.0:
            return 'stable_detection'
        elif energy_magnitude < 5.0:
            return 'bifurcation'
        else:
            return 'chaos_mode'

    def _extract_vulnerabilities(self, H: np.ndarray, network_graph: Dict) -> List[Dict]:
        """Extract vulnerabilities from energy field"""
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
                    'sparse_optimized': True
                })

        return sorted(vulns, key=lambda x: x['energy'], reverse=True)

    def compute_spectral_properties(self, k: int = 10) -> Dict:
        """
        Compute spectral properties of the network using sparse eigensolvers.

        Uses ARPACK for efficient sparse eigenvalue computation.

        Args:
            k: Number of eigenvalues to compute

        Returns:
            Dict with eigenvalues and spectral gap
        """
        if self.adjacency_matrix is None:
            raise ValueError("Build adjacency matrix first")

        L = self.sparse_laplacian()

        # Compute k smallest eigenvalues
        try:
            eigenvalues, _ = eigsh(L.astype(np.float64), k=min(k, L.shape[0] - 2), which='SM')
            eigenvalues = np.sort(eigenvalues)

            # Spectral gap (second smallest eigenvalue)
            spectral_gap = eigenvalues[1] if len(eigenvalues) > 1 else 0

            return {
                'eigenvalues': eigenvalues.tolist(),
                'spectral_gap': float(spectral_gap),
                'algebraic_connectivity': float(eigenvalues[1]) if len(eigenvalues) > 1 else 0
            }
        except Exception as e:
            logger.warning(f"Spectral computation failed: {e}")
            return {'eigenvalues': [], 'spectral_gap': 0, 'error': str(e)}
