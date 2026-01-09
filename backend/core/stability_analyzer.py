"""
Stability Analyzer - Lyapunov Methods for FDDE Systems
"""
import numpy as np
from typing import Dict, List, Optional

class StabilityAnalyzer:
    """
    Lyapunov stability analysis for Hamiltonian energy fields.
    """
    
    def __init__(self):
        self.eigenvalue_history = []
        self.stability_log = []
    
    def analyze_lyapunov(self, H: np.ndarray, H_prev: np.ndarray, jacobian: Optional[np.ndarray] = None) -> Dict:
        """
        Perform Lyapunov stability analysis.
        
        Args:
            H: Current energy state
            H_prev: Previous energy state
            jacobian: Optional precomputed Jacobian
        
        Returns:
            Stability metrics
        """
        if jacobian is None:
            jacobian = self._compute_jacobian(H, H_prev)
        
        # Eigenvalue analysis
        eigenvalues = np.linalg.eigvals(jacobian)
        self.eigenvalue_history.append(eigenvalues)
        
        # Stability criterion: max(Re(λ)) < 0
        max_real_part = np.max(np.real(eigenvalues))
        stable = max_real_part < 0
        
        # Phase classification
        energy_magnitude = np.max(np.abs(H))
        
        if energy_magnitude < 1.0:
            phase = 'stable_detection'
        elif energy_magnitude < 5.0 and not stable:
            phase = 'bifurcation'
        elif energy_magnitude >= 5.0:
            phase = 'chaos_mode'
        else:
            phase = 'converging'
        
        result = {
            'stable': stable,
            'max_eigenvalue_real': float(max_real_part),
            'energy_magnitude': float(energy_magnitude),
            'phase': phase,
            'eigenvalues': eigenvalues.tolist()
        }
        
        self.stability_log.append(result)
        return result
    
    def _compute_jacobian(self, H: np.ndarray, H_prev: np.ndarray, epsilon: float = 1e-6) -> np.ndarray:
        """Compute numerical Jacobian approximation."""
        n = min(len(H), 10)  # Sample for efficiency
        jacobian = np.zeros((n, n))
        
        for i in range(n):
            H_perturbed = H_prev.copy()
            H_perturbed[i] += epsilon
            
            # Approximate evolution (simplified)
            H_pert_evolved = H_perturbed[:n] + 0.1 * (H[:n] - H_prev[:n])
            
            # Finite difference
            jacobian[i, :] = (H_pert_evolved - H[:n]) / epsilon
        
        return jacobian
    
    def adaptive_cooling(self, H: np.ndarray, t: int, T_initial: float = 1.0) -> np.ndarray:
        """
        Simulated annealing to prevent chaos mode.
        
        T = T_initial / (1 + 0.1 * t)  # Cooling schedule
        H_cooled = H * exp(-|H| / T)
        """
        T = T_initial / (1 + 0.1 * t)
        H_cooled = H * np.exp(-np.abs(H) / T)
        return H_cooled
