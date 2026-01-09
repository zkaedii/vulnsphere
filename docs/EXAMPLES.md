# Examples & Tutorials

## Basic Usage

### Python API

```python
from backend.core.zkaedi_prime import ZKAEDIPrimeFractalEngine

# Initialize engine
engine = ZKAEDIPrimeFractalEngine(alpha=0.618)

# Define network
network = {
    '192.168.1.1': ['192.168.1.2', '192.168.1.3'],
    '192.168.1.2': ['192.168.1.1'],
    '192.168.1.3': ['192.168.1.1']
}

# Run scan
result = await engine.solve_vuln_detection_fdde(network)

print(f"Converged: {result['converged']}")
print(f"Vulnerabilities: {len(result['vulnerabilities'])}")
```

### REST API

```bash
curl -X POST http://localhost:8000/api/v1/scan/network \
  -H "Content-Type: application/json" \
  -d '{
    "192.168.1.1": ["192.168.1.2"],
    "192.168.1.2": ["192.168.1.1"]
  }'
```

## Advanced: MDM Suppression

```python
from backend.suppression.mdm_engine import MirageDelayMirage

mdm = MirageDelayMirage()

probe = {
    'id': 'probe_1',
    'target_node': '192.168.1.1',
    'energy': 5.0
}

result = await mdm.process_probe_with_mdm(probe, time_step=0)
print(result['status'])  # 'miraged' or 'terminated'
```

## Zero-Trust Moats

```python
from backend.suppression.zero_trust_moat import ZeroTrustMoat

moat = ZeroTrustMoat()

# Create moat
moat.create_moat(
    zone_id='production',
    assets=['192.168.1.1', '192.168.1.2'],
    trust_level='zero'
)

# Lower drawbridge
result = moat.lower_drawbridge(
    zone_id='production',
    requester_id='admin',
    credentials={'token': 'abc123'}
)
```

## Fractal Calculus

```python
from backend.core.fractal_calculus import FractalCalculus

calc = FractalCalculus(alpha=0.618)

# Validate proofs
results = calc.validate_proofs()
print(results)  # {'chain_rule': True, 'product_rule': True, ...}
```
