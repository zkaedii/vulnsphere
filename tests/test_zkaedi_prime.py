"""
Tests for ZKAEDI PRIME Engine
"""
import pytest
import asyncio
from backend.core.zkaedi_prime import ZKAEDIPrimeFractalEngine

@pytest.mark.asyncio
async def test_initialize_field():
    """Test Hamiltonian field initialization"""
    engine = ZKAEDIPrimeFractalEngine()
    
    network = {
        'node1': ['node2'],
        'node2': ['node1']
    }
    
    engine.initialize_field(network)
    
    assert engine.H_base is not None
    assert len(engine.H_base) == 2
    assert len(engine.nodes) == 2

@pytest.mark.asyncio
async def test_solve_vuln_detection():
    """Test vulnerability detection solver"""
    engine = ZKAEDIPrimeFractalEngine()
    
    network = {
        '192.168.1.1': ['192.168.1.2'],
        '192.168.1.2': ['192.168.1.1']
    }
    
    result = await engine.solve_vuln_detection_fdde(network, max_iterations=100)
    
    assert 'algorithm' in result
    assert 'iterations' in result
    assert 'converged' in result
    assert 'vulnerabilities' in result
    assert result['algorithm'] == 'ZKAEDI_PRIME_FRACTAL_FDDE'

def test_fractal_delay_function():
    """Test fractal delay generation"""
    engine = ZKAEDIPrimeFractalEngine()
    
    delay = engine.fractal_delay_function(0)
    assert delay > 0
    
    delay2 = engine.fractal_delay_function(1)
    assert delay2 != delay  # Should vary

def test_apply_mdm_suppression():
    """Test MDM suppression"""
    engine = ZKAEDIPrimeFractalEngine()
    
    probe = {
        'id': 'probe1',
        'energy': 5.0,
        'timestamp': 1.0
    }
    
    result = engine.apply_mdm_suppression(probe, vuln_energy=6.0)
    
    assert 'status' in result
    assert result['status'] in ['terminated', 'miraged']
