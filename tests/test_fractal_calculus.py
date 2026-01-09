"""
Tests for Fractal Calculus Module
"""
import pytest
import numpy as np
from backend.core.fractal_calculus import FractalCalculus

def test_fractal_derivative():
    """Test basic fractal derivative computation"""
    calc = FractalCalculus(alpha=0.618)
    
    def f(t):
        return t**2
    
    result = calc.fractal_derivative(f, 1.0)
    assert isinstance(result, float)
    assert result > 0

def test_chain_rule():
    """Test chain rule validation"""
    calc = FractalCalculus(alpha=0.618)
    
    u = lambda t: t**2
    g = lambda x: np.sin(x)
    
    lhs, rhs = calc.chain_rule(g, u, 1.0)
    
    # Should be approximately equal
    assert abs(lhs - rhs) < 1e-3

def test_product_rule():
    """Test product rule validation"""
    calc = FractalCalculus(alpha=0.618)
    
    f = lambda t: t**1.5
    g = lambda t: t**1.2
    
    lhs, rhs = calc.product_rule(f, g, 1.0)
    
    # Should be approximately equal
    assert abs(lhs - rhs) < 1e-3

def test_power_law():
    """Test power-law scaling"""
    calc = FractalCalculus(alpha=0.618)
    
    numerical, analytical = calc.power_law(2.0, 1.0)
    
    # Should be approximately equal
    assert abs(numerical - analytical) < 1e-2

def test_validate_proofs():
    """Test proof validation"""
    calc = FractalCalculus(alpha=0.618)
    
    results = calc.validate_proofs()
    
    assert results['chain_rule'] == True
    assert results['product_rule'] == True
    assert results['power_law'] == True
    assert results['all_valid'] == True
