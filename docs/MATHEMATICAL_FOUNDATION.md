# Mathematical Foundation

## ψ-Fractal Derivatives

The core mathematical foundation of VulnSphere PRIME is based on ψ-fractal derivatives.

### Definition

```
D^α_ψ f(t) = lim[h→0] (f(t+h) - f(t))/(ψ(t+h) - ψ(t))
```

where:
- α: Fractal order parameter (0 < α ≤ 1)
- ψ: Scaling function (typically ψ(t) = t^α)
- f: Function to differentiate

### Chain Rule

**Theorem**: Let u(t) be ψ-fractal differentiable and g(u) be classically differentiable. Then:

```
D^α_ψ [g(u(t))] = g'(u(t)) · D^α_ψ u(t)
```

**Proof**: See implementation in `backend/core/fractal_calculus.py`

### Product Rule

**Theorem**: Let f, g both be ψ-fractal differentiable. Then:

```
D^α_ψ [f(t)g(t)] = f(t) D^α_ψ g(t) + g(t) D^α_ψ f(t)
```

### Power-Law Scaling

**Theorem**: For f(t) = t^β with β > α:

```
D^α_ψ (t^β) = β·t^(β-α)
```

## Fractal Delay Differential Equations (FDDEs)

VulnSphere PRIME solves FDDEs of the form:

```
D^α_ψ x(t) = f(t, x(t), x(t - τ(t)))
```

where τ(t) is a variable delay function.

## Stability Analysis

Lyapunov stability analysis is performed using eigenvalue computation:

- System is stable if all eigenvalues have Re(λ) < 0
- Phase transitions occur at critical energy thresholds
- Chaos mode activates when energy exceeds critical threshold

## References

- Recent fractal calculus research (2020-2026)
- Lyapunov stability theory
- Delay differential equation theory
