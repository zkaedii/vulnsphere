"""
Cross-Domain Applications of ZKAEDI PRIME Fractal Calculus

This module demonstrates the versatility of the fractal calculus framework
across multiple domains:

1. Physics - Anomalous diffusion modeling
2. Finance - Rough volatility and option pricing
3. Biology - Epidemic spread modeling
4. Network Analysis - Community detection

Each application uses the same underlying ψ-fractal derivative framework.
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.fractal_calculus import FractalCalculus


@dataclass
class SimulationResult:
    """Generic result container for cross-domain simulations"""

    domain: str
    time_series: np.ndarray
    final_state: np.ndarray
    parameters: Dict
    metrics: Dict


class PhysicsApplications:
    """
    Physics applications of fractal calculus.

    Anomalous diffusion occurs in many physical systems where the
    mean squared displacement scales non-linearly with time:
    <x²(t)> ~ t^α, where α ≠ 1

    - α < 1: Subdiffusion (crowded environments, porous media)
    - α > 1: Superdiffusion (turbulence, active matter)
    """

    def __init__(self, alpha: float = 0.618):
        self.alpha = alpha
        self.fc = FractalCalculus(alpha=alpha)

    def simulate_anomalous_diffusion(
        self, n_particles: int = 1000, n_steps: int = 1000, diffusion_coeff: float = 1.0
    ) -> SimulationResult:
        """
        Simulate anomalous diffusion using fractal Brownian motion.

        The particle positions evolve according to a fractional
        Langevin equation with memory effects.
        """
        # Initialize particle positions
        positions = np.zeros((n_particles, n_steps))
        velocities = np.zeros(n_particles)

        dt = 0.01
        gamma = 1.0  # Friction coefficient

        for t in range(1, n_steps):
            # Fractal noise (correlated random walk)
            # Scale noise by t^(α-1) for anomalous scaling
            t_scaled = t * dt
            if t_scaled > 0:
                noise_scale = diffusion_coeff * (t_scaled ** (self.alpha - 1))
            else:
                noise_scale = diffusion_coeff

            noise = np.random.normal(0, noise_scale, n_particles)

            # Fractional Langevin dynamics
            velocities = velocities * np.exp(-gamma * dt) + noise
            positions[:, t] = positions[:, t - 1] + velocities * dt

        # Calculate mean squared displacement
        msd = np.mean(positions**2, axis=0)
        times = np.arange(n_steps) * dt

        # Fit to verify anomalous scaling
        # MSD ~ D * t^α
        log_times = np.log(times[1:] + 1e-10)
        log_msd = np.log(msd[1:] + 1e-10)
        fitted_alpha = np.polyfit(log_times[:100], log_msd[:100], 1)[0]

        return SimulationResult(
            domain="physics",
            time_series=msd,
            final_state=positions[:, -1],
            parameters={
                "alpha": self.alpha,
                "n_particles": n_particles,
                "diffusion_coeff": diffusion_coeff,
            },
            metrics={
                "fitted_alpha": fitted_alpha,
                "final_msd": msd[-1],
                "spread_std": np.std(positions[:, -1]),
            },
        )


class FinanceApplications:
    """
    Finance applications of fractal calculus.

    Financial markets exhibit rough volatility - volatility itself
    has fractal properties with Hurst exponent H ≈ 0.1.

    This leads to fractional stochastic volatility models that
    better capture empirical market behavior.
    """

    def __init__(self, alpha: float = 0.618, hurst: float = 0.1):
        self.alpha = alpha
        self.hurst = hurst
        self.fc = FractalCalculus(alpha=alpha)

    def simulate_rough_volatility(
        self,
        n_days: int = 252,
        initial_vol: float = 0.2,
        mean_reversion: float = 2.0,
        vol_of_vol: float = 0.3,
    ) -> SimulationResult:
        """
        Simulate rough volatility model (rBergomi-style).

        The variance process follows a fractional Ornstein-Uhlenbeck:
        dV_t = κ(θ - V_t)dt + ξ V_t^γ dW_t^H

        where W^H is fractional Brownian motion with Hurst H < 0.5.
        """
        dt = 1 / 252
        variance = np.zeros(n_days)
        variance[0] = initial_vol**2

        # Generate fractional Brownian motion increments
        fbm_increments = self._generate_fbm_increments(n_days - 1, dt)

        theta = initial_vol**2  # Long-term variance

        for t in range(1, n_days):
            # Fractional Ornstein-Uhlenbeck dynamics
            drift = mean_reversion * (theta - variance[t - 1])
            diffusion = vol_of_vol * np.sqrt(max(variance[t - 1], 0))

            variance[t] = max(
                variance[t - 1] + drift * dt + diffusion * fbm_increments[t - 1],
                1e-8,  # Floor to prevent negative variance
            )

        volatility = np.sqrt(variance)

        return SimulationResult(
            domain="finance",
            time_series=volatility,
            final_state=variance,
            parameters={
                "hurst": self.hurst,
                "mean_reversion": mean_reversion,
                "vol_of_vol": vol_of_vol,
            },
            metrics={
                "realized_vol": np.mean(volatility),
                "vol_of_vol_realized": np.std(volatility),
                "min_vol": np.min(volatility),
                "max_vol": np.max(volatility),
            },
        )

    def _generate_fbm_increments(self, n: int, dt: float) -> np.ndarray:
        """Generate fractional Brownian motion increments using Cholesky"""
        H = self.hurst

        # Covariance matrix for fBm
        t = np.arange(1, n + 2) * dt
        cov = np.zeros((n + 1, n + 1))

        for i in range(n + 1):
            for j in range(n + 1):
                cov[i, j] = 0.5 * (
                    t[i] ** (2 * H) + t[j] ** (2 * H) - abs(t[i] - t[j]) ** (2 * H)
                )

        # Add small diagonal for numerical stability
        cov += 1e-10 * np.eye(n + 1)

        # Cholesky decomposition
        try:
            L = np.linalg.cholesky(cov)
            Z = np.random.normal(0, 1, n + 1)
            fbm = L @ Z
            return np.diff(fbm)
        except np.linalg.LinAlgError:
            # Fallback to standard Brownian if Cholesky fails
            return np.random.normal(0, np.sqrt(dt), n)


class BiologyApplications:
    """
    Biology applications of fractal calculus.

    Epidemic spread often exhibits non-Markovian dynamics due to
    memory effects (latent periods, behavioral changes).

    Fractional SIR models capture these effects.
    """

    def __init__(self, alpha: float = 0.9):
        self.alpha = alpha
        self.fc = FractalCalculus(alpha=alpha)

    def simulate_fractional_sir(
        self,
        population: int = 10000,
        initial_infected: int = 10,
        beta: float = 0.3,
        gamma: float = 0.1,
        n_days: int = 200,
    ) -> SimulationResult:
        """
        Simulate fractional SIR epidemic model.

        The fractional SIR model:
        D^α S = -β S I / N
        D^α I = β S I / N - γ I
        D^α R = γ I

        where D^α is the Caputo fractional derivative.
        Memory effects lead to slower epidemic dynamics.
        """
        N = population
        dt = 0.1

        # Initialize compartments
        S = np.zeros(n_days)
        I = np.zeros(n_days)
        R = np.zeros(n_days)

        S[0] = N - initial_infected
        I[0] = initial_infected
        R[0] = 0

        # History for fractional derivative approximation
        S_history = [S[0]]
        I_history = [I[0]]
        R_history = [R[0]]

        for t in range(1, n_days):
            # Grünwald-Letnikov fractional derivative approximation
            # Uses history with decaying weights
            weights = self._grunwald_weights(len(S_history), self.alpha)

            # Weighted sum of history
            dS_frac = sum(w * sh for w, sh in zip(weights, reversed(S_history)))
            dI_frac = sum(w * ih for w, ih in zip(weights, reversed(I_history)))

            # SIR dynamics with fractional derivative
            infection_rate = beta * S[t - 1] * I[t - 1] / N
            recovery_rate = gamma * I[t - 1]

            S[t] = max(0, S[t - 1] - dt**self.alpha * infection_rate + 0.01 * dS_frac)
            I[t] = max(
                0,
                I[t - 1]
                + dt**self.alpha * (infection_rate - recovery_rate)
                + 0.01 * dI_frac,
            )
            R[t] = N - S[t] - I[t]

            S_history.append(S[t])
            I_history.append(I[t])
            R_history.append(R[t])

            # Limit history length for efficiency
            if len(S_history) > 100:
                S_history = S_history[-100:]
                I_history = I_history[-100:]
                R_history = R_history[-100:]

        peak_infected = np.max(I)
        peak_day = np.argmax(I)
        total_infected = N - S[-1]

        return SimulationResult(
            domain="biology",
            time_series=I,  # Infected curve
            final_state=np.array([S[-1], I[-1], R[-1]]),
            parameters={
                "alpha": self.alpha,
                "beta": beta,
                "gamma": gamma,
                "population": population,
            },
            metrics={
                "peak_infected": peak_infected,
                "peak_day": peak_day,
                "total_infected": total_infected,
                "attack_rate": total_infected / N,
                "R0_effective": beta / gamma,
            },
        )

    def _grunwald_weights(self, n: int, alpha: float) -> List[float]:
        """Calculate Grünwald-Letnikov weights for fractional derivative"""
        weights = [1.0]
        for k in range(1, n):
            weights.append(weights[-1] * (alpha - k + 1) / k)
        return weights


class NetworkApplications:
    """
    Network analysis applications using fractal dynamics.

    Fractal calculus can identify community structure through
    diffusion dynamics on graphs.
    """

    def __init__(self, alpha: float = 0.618):
        self.alpha = alpha
        self.fc = FractalCalculus(alpha=alpha)

    def detect_communities(
        self, adjacency: np.ndarray, n_communities: int = 3, n_iterations: int = 1000
    ) -> SimulationResult:
        """
        Community detection using fractal diffusion.

        Nodes in the same community will have similar
        energy values after fractal diffusion.
        """
        n_nodes = adjacency.shape[0]

        # Compute Laplacian
        degrees = adjacency.sum(axis=1)
        D = np.diag(degrees)
        L = D - adjacency

        # Initialize random energy field
        H = np.random.rand(n_nodes) * 0.1
        H_history = [H.copy()]

        eta = 0.4
        sigma = 0.05

        for t in range(n_iterations):
            # Fractal diffusion on graph
            diffusion = -L @ H

            # Nonlinear response
            sigmoid = 1 / (1 + np.exp(-0.3 * H))

            # Update with fractal memory
            if t > 0:
                h = sigma
                t_scaled = t * h
                delta_psi = (t_scaled + h) ** self.alpha - t_scaled**self.alpha
                if abs(delta_psi) < 1e-10:
                    delta_psi = 1e-10
                fractal_deriv = (H - H_history[-1]) / delta_psi
                H = H + eta * fractal_deriv * sigmoid + 0.01 * diffusion
            else:
                H = H + eta * H * sigmoid + 0.01 * diffusion

            H_history.append(H.copy())

            # Check convergence
            if t > 100 and np.max(np.abs(H - H_history[-2])) < 1e-6:
                break

        # Cluster based on energy values
        from scipy.cluster.hierarchy import fcluster, linkage

        energy_matrix = H.reshape(-1, 1)
        linkage_matrix = linkage(energy_matrix, method="ward")
        communities = fcluster(linkage_matrix, n_communities, criterion="maxclust")

        return SimulationResult(
            domain="network",
            time_series=np.array([np.mean(h) for h in H_history]),
            final_state=H,
            parameters={
                "alpha": self.alpha,
                "n_communities": n_communities,
                "n_nodes": n_nodes,
            },
            metrics={
                "iterations": t + 1,
                "communities": communities.tolist(),
                "modularity_proxy": np.std(H),  # Higher = better separation
            },
        )


async def main():
    """Run cross-domain demonstrations"""
    print("=" * 60)
    print("ZKAEDI PRIME - Cross-Domain Applications")
    print("=" * 60)

    # 1. Physics: Anomalous Diffusion
    print("\n1. PHYSICS: Anomalous Diffusion Simulation")
    print("-" * 40)
    physics = PhysicsApplications(alpha=0.7)
    result = physics.simulate_anomalous_diffusion(n_particles=500, n_steps=500)
    print(f"   Target α: {result.parameters['alpha']}")
    print(f"   Fitted α: {result.metrics['fitted_alpha']:.3f}")
    print(f"   Final MSD: {result.metrics['final_msd']:.4f}")

    # 2. Finance: Rough Volatility
    print("\n2. FINANCE: Rough Volatility Simulation")
    print("-" * 40)
    finance = FinanceApplications(hurst=0.1)
    result = finance.simulate_rough_volatility(n_days=252)
    print(f"   Hurst parameter: {result.parameters['hurst']}")
    print(f"   Realized volatility: {result.metrics['realized_vol']:.4f}")
    print(f"   Vol-of-vol: {result.metrics['vol_of_vol_realized']:.4f}")
    print(
        f"   Vol range: [{result.metrics['min_vol']:.4f}, {result.metrics['max_vol']:.4f}]"
    )

    # 3. Biology: Fractional SIR
    print("\n3. BIOLOGY: Fractional SIR Epidemic Model")
    print("-" * 40)
    biology = BiologyApplications(alpha=0.85)
    result = biology.simulate_fractional_sir(population=10000, initial_infected=10)
    print(f"   Fractional order: {result.parameters['alpha']}")
    print(
        f"   Peak infected: {result.metrics['peak_infected']:.0f} (day {result.metrics['peak_day']})"
    )
    print(f"   Total attack rate: {result.metrics['attack_rate']*100:.1f}%")
    print(f"   Effective R0: {result.metrics['R0_effective']:.2f}")

    # 4. Network: Community Detection
    print("\n4. NETWORK: Fractal Community Detection")
    print("-" * 40)
    # Create sample network with community structure
    n = 30
    adj = np.zeros((n, n))
    # Community 1: nodes 0-9
    for i in range(10):
        for j in range(i + 1, 10):
            if np.random.rand() < 0.7:
                adj[i, j] = adj[j, i] = 1
    # Community 2: nodes 10-19
    for i in range(10, 20):
        for j in range(i + 1, 20):
            if np.random.rand() < 0.7:
                adj[i, j] = adj[j, i] = 1
    # Community 3: nodes 20-29
    for i in range(20, 30):
        for j in range(i + 1, 30):
            if np.random.rand() < 0.7:
                adj[i, j] = adj[j, i] = 1
    # Inter-community edges (sparse)
    for _ in range(5):
        i, j = np.random.randint(0, 10), np.random.randint(10, 20)
        adj[i, j] = adj[j, i] = 1
        i, j = np.random.randint(10, 20), np.random.randint(20, 30)
        adj[i, j] = adj[j, i] = 1

    network = NetworkApplications(alpha=0.618)
    result = network.detect_communities(adj, n_communities=3)
    print(f"   Nodes: {result.parameters['n_nodes']}")
    print(f"   Iterations to converge: {result.metrics['iterations']}")
    print(f"   Community separation: {result.metrics['modularity_proxy']:.4f}")

    print("\n" + "=" * 60)
    print("Cross-domain demonstrations complete!")
    print("The fractal calculus framework adapts to each domain.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
