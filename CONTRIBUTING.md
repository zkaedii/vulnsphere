# Contributing to VulnSphere PRIME

Thank you for your interest in contributing to VulnSphere PRIME! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional, for containerized development)
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/vulnsphere-prime.git
   cd vulnsphere-prime
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/zkaedi/vulnsphere-prime.git
   ```

## Development Setup

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-asyncio black isort mypy

# Set PYTHONPATH
export PYTHONPATH=$(pwd)
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Docker Setup (Alternative)

```bash
docker-compose up -d
```

## Making Changes

### Branch Naming Convention

- `feature/` - New features (e.g., `feature/sparse-hamiltonian`)
- `fix/` - Bug fixes (e.g., `fix/quantum-rng-fallback`)
- `docs/` - Documentation updates (e.g., `docs/api-reference`)
- `refactor/` - Code refactoring (e.g., `refactor/engine-base-class`)
- `test/` - Test additions/modifications (e.g., `test/engine-coverage`)

### Workflow

1. Create a new branch from `main`:
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our [Coding Standards](#coding-standards)

3. Run tests to ensure nothing is broken:
   ```bash
   pytest tests/ -v
   ```

4. Commit your changes with a descriptive message:
   ```bash
   git add .
   git commit -m "feat: add sparse Hamiltonian for memory optimization"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Open a Pull Request

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(engine): add sparse Hamiltonian support for large networks
fix(quantum): resolve RNG fallback issue in QuantumSafeRNG
docs(readme): clarify performance benchmark methodology
test(boosted): add convergence tests for ZKAEDIPrimeBoosted
```

## Pull Request Process

1. **Title**: Use the same format as commit messages
2. **Description**: Include:
   - Summary of changes
   - Motivation/context
   - How to test
   - Screenshots (if UI changes)

3. **Checklist** (include in PR description):
   ```markdown
   - [ ] Tests pass locally (`pytest tests/ -v`)
   - [ ] Code follows project style guidelines
   - [ ] Documentation updated (if applicable)
   - [ ] No new security vulnerabilities introduced
   ```

4. **Review**: Wait for at least one maintainer approval

5. **Merge**: Maintainers will merge using squash-and-merge

## Coding Standards

### Python

- **Style**: Follow PEP 8, enforced by Black
- **Type Hints**: Required for all public functions
- **Docstrings**: Google style for all public functions/classes

```python
def calculate_energy(H: np.ndarray, gamma: float = 0.3) -> float:
    """
    Calculate the total energy of the Hamiltonian field.

    Args:
        H: The Hamiltonian energy field array.
        gamma: Nonlinear attractor sharpening coefficient.

    Returns:
        Total energy magnitude as a float.

    Raises:
        ValueError: If H contains NaN values.
    """
    if np.any(np.isnan(H)):
        raise ValueError("Hamiltonian contains NaN values")
    return float(np.sum(np.abs(H) ** gamma))
```

- **Formatting**:
  ```bash
  black backend/ tests/
  isort backend/ tests/
  ```

- **Type Checking**:
  ```bash
  mypy backend/ --ignore-missing-imports
  ```

### JavaScript/React

- **Style**: ESLint + Prettier
- **Components**: Functional components with hooks
- **Formatting**:
  ```bash
  cd frontend
  npm run lint
  npm run format
  ```

### File Organization

```
backend/
├── core/           # Core engine implementations
├── api/            # FastAPI routes
├── scanners/       # Security scanner integrations
├── suppression/    # Suppression engines
├── utils/          # Utility functions
└── config.py       # Configuration

tests/
├── test_*.py       # Test files mirror backend structure
└── fixtures/       # Test fixtures and data

frontend/
├── src/
│   ├── components/ # React components
│   ├── hooks/      # Custom hooks
│   └── utils/      # Frontend utilities
└── public/
```

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=backend --cov-report=html

# Specific test file
pytest tests/test_zkaedi_engines.py -v

# Specific test
pytest tests/test_zkaedi_engines.py::TestZKAEDIPrimeBoosted::test_adaptive_eta_decay -v
```

### Writing Tests

- Use `pytest` with `pytest-asyncio` for async tests
- Each test should be independent
- Use fixtures for common setup
- Test edge cases and error conditions

```python
import pytest
import numpy as np
from backend.core.zkaedi_prime_boosted import ZKAEDIPrimeBoosted

@pytest.fixture
def engine():
    return ZKAEDIPrimeBoosted(alpha=0.618, eta=0.4)

@pytest.mark.asyncio
async def test_solve_small_network(engine):
    """Test solving a small network converges correctly."""
    network = {
        '192.168.1.1': ['192.168.1.2'],
        '192.168.1.2': ['192.168.1.1']
    }

    result = await engine.solve_vuln_detection_boosted(
        network_graph=network,
        max_iterations=1000
    )

    assert result.steps > 0
    assert result.converged or result.steps < 1000
    assert len(result.vulnerabilities) >= 0
```

### Test Coverage Requirements

- New features should include tests
- Aim for >80% coverage on new code
- Critical paths (engines, security) should have >90% coverage

## Documentation

### Code Documentation

- All public functions need docstrings
- Complex algorithms should have inline comments
- Update relevant markdown files when changing behavior

### Updating Documentation

1. **README.md**: Update for new features or changed behavior
2. **docs/**: Update API reference, guides as needed
3. **Code comments**: Explain complex logic inline

## Areas for Contribution

### Good First Issues

- Add more test coverage
- Improve documentation
- Fix typos and formatting
- Add type hints to untyped code

### Intermediate

- Implement scanner integrations (Trivy, ZAP, Nmap)
- Add new visualization features
- Performance optimizations
- Frontend improvements

### Advanced

- Sparse Hamiltonian implementation
- MPI distributed computing
- GPU acceleration
- New mathematical models

## Mathematical Contributions

If contributing mathematical proofs or algorithms:
- Include rigorous proofs
- Provide test cases
- Document assumptions and limitations
- Reference relevant academic literature

## Security

- Do not commit secrets or API keys
- Report security issues privately via email
- Follow responsible disclosure practices
- Run security scans before submitting PRs

## Questions?

- Open a [GitHub Discussion](https://github.com/zkaedi/vulnsphere-prime/discussions)
- Tag maintainers in issues for clarification
- Check existing issues/PRs for similar topics

---

Thank you for contributing to VulnSphere PRIME!
