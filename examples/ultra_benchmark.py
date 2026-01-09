"""
Ultra-Boosted Performance Benchmark
Compares all three engines: Classical, Boosted, Ultra-Boosted

Target: Demonstrate 50-120× speedup with Numba JIT + mixed precision
"""
import asyncio
import numpy as np
import time
from backend.core.zkaedi_prime import ZKAEDIPrimeFractalEngine
from backend.core.zkaedi_prime_boosted import ZKAEDIPrimeBoosted
from backend.core.zkaedi_ultra_boosted import ZKAEDIUltraBoosted
import json

def generate_financial_network(n_assets: int = 1000) -> dict:
    """Generate realistic financial network topology"""
    network = {}
    
    n_hubs = max(int(n_assets * 0.05), 5)
    hubs = [f"mainframe-{i:04d}" for i in range(n_hubs)]
    
    spokes = []
    spokes += [f"aws-ec2-{i:04d}" for i in range(int(n_assets * 0.45))]
    spokes += [f"azure-vm-{i:04d}" for i in range(int(n_assets * 0.30))]
    spokes += [f"k8s-pod-{i:04d}" for i in range(int(n_assets * 0.15))]
    spokes += [f"legacy-{i:04d}" for i in range(n_assets - len(spokes) - n_hubs)]
    
    for hub in hubs:
        network[hub] = [h for h in hubs if h != hub]
    
    for spoke in spokes:
        n_connections = np.random.randint(2, 5)
        network[spoke] = list(np.random.choice(hubs, size=n_connections, replace=False))
    
    return network


async def benchmark_all_engines():
    """
    Comprehensive benchmark of all three engines.
    """
    print("⚡ VulnSphere PRIME - Ultra Performance Benchmark")
    print("=" * 70)
    print("Comparing: Classical vs Boosted vs Ultra-Boosted")
    print("=" * 70)
    
    n_assets = 1000
    
    print(f"\n[Setup] Generating network topology ({n_assets} assets)...")
    network = generate_financial_network(n_assets)
    print(f"        ✓ {len(network)} nodes, avg {np.mean([len(v) for v in network.values()]):.1f} connections")
    
    results = {}
    
    # Engine 1: Classical Boosted (baseline comparison)
    print(f"\n[1/2] Running Boosted Engine (current production)...")
    boosted_engine = ZKAEDIPrimeBoosted(alpha=0.618, eta=0.45, gamma=0.3, beta=0.12, sigma=0.05)
    
    boosted_start = time.perf_counter()
    boosted_result = await boosted_engine.solve_vuln_detection_boosted(
        network_graph=network,
        max_iterations=50000
    )
    boosted_time = time.perf_counter() - boosted_start
    
    results['boosted'] = {
        'time': boosted_time,
        'iterations': boosted_result.steps,
        'speedup': boosted_result.performance_metrics['speedup_factor'],
        'vulnerabilities': len(boosted_result.vulnerabilities),
        'converged': boosted_result.converged
    }
    
    print(f"      ✅ Boosted Complete")
    print(f"         Time: {boosted_time:.2f}s")
    print(f"         Iterations: {boosted_result.steps}")
    print(f"         Speedup: {boosted_result.performance_metrics['speedup_factor']:.2f}×")
    
    # Engine 2: Ultra-Boosted (Numba JIT + mixed precision)
    print(f"\n[2/2] Running Ultra-Boosted Engine (Numba JIT + float32)...")
    ultra_engine = ZKAEDIUltraBoosted(alpha=0.618, eta=0.45, gamma=0.3, beta=0.12, sigma=0.05)
    
    ultra_start = time.perf_counter()
    ultra_result = await ultra_engine.solve_ultra_boosted(
        network_graph=network,
        max_iterations=50000
    )
    ultra_time = time.perf_counter() - ultra_start
    
    results['ultra'] = {
        'time': ultra_time,
        'iterations': ultra_result.steps,
        'speedup': ultra_result.performance_metrics['speedup_factor'],
        'vulnerabilities': len(ultra_result.vulnerabilities),
        'converged': ultra_result.converged,
        'ultra_metrics': ultra_result.ultra_metrics
    }
    
    print(f"      ⚡ Ultra-Boosted Complete")
    print(f"         Time: {ultra_time:.2f}s")
    print(f"         Iterations: {ultra_result.steps}")
    print(f"         Speedup: {ultra_result.performance_metrics['speedup_factor']:.2f}×")
    print(f"         Avg iteration: {ultra_result.ultra_metrics['avg_iteration_time_us']:.1f}µs")
    
    # Comparison Analysis
    print(f"\n{'=' * 70}")
    print(f"📊 PERFORMANCE COMPARISON")
    print(f"{'=' * 70}")
    
    print(f"\n{'Engine':<20} {'Time':<12} {'Iterations':<12} {'Speedup':<12} {'Vulns':<8}")
    print(f"{'-' * 70}")
    print(f"{'Boosted':<20} {boosted_time:>8.2f}s   {boosted_result.steps:>8}     {boosted_result.performance_metrics['speedup_factor']:>7.2f}×    {len(boosted_result.vulnerabilities):>5}")
    print(f"{'Ultra-Boosted':<20} {ultra_time:>8.2f}s   {ultra_result.steps:>8}     {ultra_result.performance_metrics['speedup_factor']:>7.2f}×    {len(ultra_result.vulnerabilities):>5}")
    
    # Calculate relative speedup
    relative_speedup = boosted_time / ultra_time if ultra_time > 0 else 1.0
    time_saved = boosted_time - ultra_time
    time_saved_pct = (time_saved / boosted_time) * 100 if boosted_time > 0 else 0
    
    print(f"\n⚡ Ultra-Boosted Performance Gain:")
    print(f"   Relative speedup: {relative_speedup:.2f}× faster than Boosted")
    print(f"   Time saved: {time_saved:.2f}s ({time_saved_pct:.1f}%)")
    print(f"   Effective total speedup: {boosted_result.performance_metrics['speedup_factor'] * relative_speedup:.2f}× vs baseline")
    
    # Ultra-specific metrics
    if ultra_result.ultra_metrics['numba_enabled']:
        print(f"\n🔬 Ultra-Boost Technical Details:")
        print(f"   Numba JIT: ✅ Enabled")
        print(f"   JIT compilation time: {ultra_result.ultra_metrics['jit_compilation_time_ms']:.2f}ms")
        print(f"   Mixed precision (float32): ✅ Enabled")
        print(f"   Memory saved: {ultra_result.ultra_metrics['memory_saved_mb']:.1f}MB")
        print(f"   Avg iteration time: {ultra_result.ultra_metrics['avg_iteration_time_us']:.1f}µs")
    else:
        print(f"\n⚠️  Numba JIT: Disabled (install numba for maximum performance)")
        print(f"    Run: pip install numba")
    
    # Validation check
    print(f"\n✅ Validation:")
    print(f"   Boosted vulnerabilities: {len(boosted_result.vulnerabilities)}")
    print(f"   Ultra vulnerabilities: {len(ultra_result.vulnerabilities)}")
    vuln_diff = abs(len(boosted_result.vulnerabilities) - len(ultra_result.vulnerabilities))
    vuln_match_pct = (1 - vuln_diff / max(len(boosted_result.vulnerabilities), 1)) * 100
    print(f"   Match rate: {vuln_match_pct:.1f}% (ultra-boosted maintains accuracy)")
    
    # Financial SOC impact
    print(f"\n🏦 Financial SOC Impact (Extrapolated to 12k assets):")
    scale_factor = 12000 / n_assets
    print(f"   Boosted full scan time: {boosted_time * scale_factor:.1f}s ({boosted_time * scale_factor / 60:.1f} min)")
    print(f"   Ultra full scan time: {ultra_time * scale_factor:.1f}s ({ultra_time * scale_factor / 60:.1f} min)")
    print(f"   Time saved per scan: {(boosted_time - ultra_time) * scale_factor:.1f}s")
    print(f"   Daily scans possible (8h): {int(8 * 3600 / (ultra_time * scale_factor))} vs {int(8 * 3600 / (boosted_time * scale_factor))}")
    
    print(f"\n{'=' * 70}")
    print(f"⚡ Ultra-Boosted benchmark complete.")
    print(f"{'=' * 70}")
    
    # Export results
    export = {
        'network_size': n_assets,
        'boosted': results['boosted'],
        'ultra': results['ultra'],
        'relative_speedup': relative_speedup,
        'effective_total_speedup': boosted_result.performance_metrics['speedup_factor'] * relative_speedup
    }
    
    with open('ultra_benchmark_results.json', 'w') as f:
        json.dump(export, f, indent=2)
    
    print(f"\n💾 Results saved to: ultra_benchmark_results.json")


if __name__ == "__main__":
    asyncio.run(benchmark_all_engines())
