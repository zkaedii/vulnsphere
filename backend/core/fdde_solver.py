"""
Fractal Delay Differential Equation (FDDE) Solver
"""
import numpy as np
from typing import Callable, Dict, Tuple, Optional

class FDDESolver:
    """
    Solver for Fractal Delay Differential Equations.
    
    Solves: D^α_ψ x(t) = f(t, x(t), x(t - τ(t)))
    """
    
    def __init__(self, alpha: float = 0.618):
        """
        Initialize FDDE solver.
        
        Args:
            alpha: Fractal order parameter
        """
        self.alpha = alpha
        self.psi_func = lambda t: t**alpha if t > 0 else 0
    
    def solve_method_of_steps(
        self,
        f: Callable,
        tau: float,
        phi: Callable,
        t_max: float,
        dt: float = 0.01
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Solve FDDE using method of steps.
        
        Args:
            f: Right-hand side function f(t, x, x_delayed)
            tau: Delay (constant)
            phi: Initial condition on [-τ, 0]
            t_max: Final time
            dt: Time step
        
        Returns:
            (time_array, solution_array)
        """
        n_steps = int(t_max / dt)
        t = np.linspace(0, t_max, n_steps)
        x = np.zeros(n_steps)
        
        # Initialize from phi
        delay_steps = int(tau / dt)
        for i in range(min(delay_steps, n_steps)):
            x[i] = phi(t[i] - tau)
        
        # Method of steps: solve on each interval [n·τ, (n+1)·τ]
        for i in range(1, n_steps):
            # Fractal derivative approximation
            h = dt
            delta_psi = self.psi_func(t[i]) - self.psi_func(t[i-1])
            
            if abs(delta_psi) < 1e-10:
                delta_psi = 1e-10
            
            # Get delayed value
            delay_idx = max(0, i - delay_steps)
            x_delayed = x[delay_idx]
            
            # ψ-fractal derivative ≈ (x[i] - x[i-1]) / delta_psi = f(...)
            # Rearrange: x[i] = x[i-1] + delta_psi * f(...)
            x[i] = x[i-1] + delta_psi * f(t[i], x[i-1], x_delayed)
        
        return t, x
    
    def analyze_stability(
        self,
        A: np.ndarray,
        B: np.ndarray,
        tau: float
    ) -> Dict:
        """
        Stability analysis for linear FDDE:
        D^α_ψ x(t) = A·x(t) + B·x(t-τ)
        
        Args:
            A: System matrix
            B: Delay matrix
            tau: Delay
        
        Returns:
            Dict with stability results
        """
        # Characteristic equation: det(s^α I - A - B·exp(-s^α τ)) = 0
        # Simplified numerical search
        eigenvalues = []
        
        for s_real in np.linspace(-10, 10, 1000):
            s_alpha = s_real**self.alpha if s_real > 0 else 0
            char_eq = np.linalg.det(
                s_alpha * np.eye(len(A)) - A - B * np.exp(-s_alpha * tau)
            )
            if abs(char_eq) < 0.01:
                eigenvalues.append(s_real)
        
        # Stability: all eigenvalues must have Re(λ) < 0
        stable = all(s < 0 for s in eigenvalues)
        
        return {
            'stable': stable,
            'eigenvalues': eigenvalues,
            'max_real_part': max(eigenvalues) if eigenvalues else None
        }
