"""
Type Definitions for ZKAEDI PRIME

Provides TypedDict definitions for all result types,
ensuring type safety and IDE autocompletion.
"""
from typing import TypedDict, List, Dict, Optional, Any
from typing_extensions import NotRequired
import numpy as np
from numpy.typing import NDArray


class VulnerabilityDict(TypedDict):
    """Single vulnerability detection result"""
    node_id: str
    energy: float
    severity: str  # 'critical', 'high', 'medium', 'low'
    neighbors: List[str]
    risk_score: int
    quantum_verified: NotRequired[bool]
    ultra_optimized: NotRequired[bool]
    sparse_optimized: NotRequired[bool]


class StabilityLogEntry(TypedDict):
    """Entry in stability analysis log"""
    iteration: int
    phase: str  # 'stable_detection', 'bifurcation', 'chaos_mode', 'converging'
    energy: float
    max_energy: float
    current_eta: float
    integrity_hash: NotRequired[str]


class PerformanceMetrics(TypedDict):
    """Performance metrics from scan"""
    iterations_saved: int
    chaos_boosts_triggered: int
    early_stops: int
    avg_eta: float
    max_energy_peak: float
    total_iterations: int
    speedup_factor: float
    memory_saved_mb: NotRequired[float]


class UltraMetrics(TypedDict):
    """Ultra-boosted engine specific metrics"""
    jit_compilation_time_ms: float
    avg_iteration_time_us: float
    numba_enabled: bool
    mixed_precision: bool
    memory_saved_mb: float


class QuantumMetrics(TypedDict):
    """Quantum-resistant engine specific metrics"""
    quantum_noise_calls: int
    signature_verifications: int
    hash_checks: int
    classical_fallbacks: int
    avg_quantum_overhead_ms: float


class BaseSolutionDict(TypedDict):
    """Base solution structure"""
    algorithm: str
    steps: int
    time_taken: float
    converged: bool
    vulnerabilities: List[VulnerabilityDict]
    stability_log: List[StabilityLogEntry]
    performance_metrics: PerformanceMetrics


class EnhancedSolutionDict(BaseSolutionDict):
    """Enhanced solution from boosted engine"""
    final_energy: Any  # np.ndarray - can't use NDArray in TypedDict
    optimal: bool
    path: List[Any]


class UltraSolutionDict(BaseSolutionDict):
    """Ultra-boosted solution"""
    final_energy: Any
    optimal: bool
    path: List[Any]
    ultra_metrics: UltraMetrics


class QuantumSolutionDict(BaseSolutionDict):
    """Quantum-resistant solution"""
    final_energy: Any
    optimal: bool
    path: List[Any]
    quantum_metrics: QuantumMetrics


class SparseSolutionDict(TypedDict):
    """Sparse Hamiltonian solution"""
    energy_field: Any
    steps: int
    time_taken: float
    converged: bool
    memory_usage_mb: float
    sparsity: float
    vulnerabilities: List[VulnerabilityDict]
    performance_metrics: PerformanceMetrics


class NetworkGraphDict(TypedDict):
    """Network graph input format"""
    nodes: NotRequired[List[str]]
    edges: NotRequired[List[Dict[str, str]]]
    adjacency: NotRequired[Dict[str, List[str]]]


class ScanRequestDict(TypedDict):
    """Scan request parameters"""
    network_graph: Dict[str, List[str]]
    max_iterations: NotRequired[int]
    engine: NotRequired[str]  # 'boosted', 'ultra', 'quantum', 'sparse'
    options: NotRequired[Dict[str, Any]]


class ScanResponseDict(TypedDict):
    """Scan response format"""
    scan_id: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    started_at: str
    completed_at: NotRequired[str]
    result: NotRequired[BaseSolutionDict]
    error: NotRequired[str]


class BatchScanRequestDict(TypedDict):
    """Batch scan request"""
    networks: List[Dict[str, List[str]]]
    max_iterations: NotRequired[int]
    engine: NotRequired[str]
    parallel: NotRequired[bool]


class BatchScanResponseDict(TypedDict):
    """Batch scan response"""
    batch_id: str
    total_networks: int
    completed: int
    failed: int
    results: List[ScanResponseDict]


class ReportRequestDict(TypedDict):
    """Report generation request"""
    scan_id: str
    format: str  # 'html', 'pdf', 'json', 'markdown'
    include_charts: NotRequired[bool]
    network_info: NotRequired[Dict[str, Any]]


class AuthTokenDict(TypedDict):
    """Authentication token"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: NotRequired[str]


class UserDict(TypedDict):
    """User information"""
    username: str
    email: NotRequired[str]
    full_name: NotRequired[str]
    disabled: bool
    scopes: List[str]


class HealthCheckDict(TypedDict):
    """Health check response"""
    status: str
    version: str
    active_scans: int
    websocket_connections: int
    database_connected: bool
    redis_connected: bool


class ErrorResponseDict(TypedDict):
    """Error response format"""
    error: str
    detail: str
    status_code: int
    correlation_id: NotRequired[str]


# Type aliases for common patterns
NetworkGraph = Dict[str, List[str]]
EnergyField = NDArray[np.float64]
ScanResult = EnhancedSolutionDict | UltraSolutionDict | QuantumSolutionDict | SparseSolutionDict
