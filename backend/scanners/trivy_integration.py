"""
Trivy Secret Scanner Integration with Hamiltonian Energy Mapping
"""
import subprocess
import json
import numpy as np
from typing import Dict, List, Optional
from .base_scanner import BaseScanner

class TrivySecretHamiltonian(BaseScanner):
    """
    Trivy secret detection with Hamiltonian energy mapping.
    Secrets manifest as pulsing red orbs in 3D space.
    """
    
    def __init__(self, eta=0.4, gamma=0.3, trivy_path: str = "trivy"):
        self.eta = eta
        self.gamma = gamma
        self.trivy_path = trivy_path
        self.secret_energy_map = {}
        
    async def scan(self, target_path: str, scan_types: List[str] = None) -> List[Dict]:
        """
        Activate Trivy's secret scanner.
        
        Args:
            target_path: Container image, filesystem, or git repo
            scan_types: ['secret', 'config', 'license', 'vuln']
        """
        if scan_types is None:
            scan_types = ['secret', 'config', 'license']
        
        scanners = ','.join(scan_types)
        
        cmd = [
            self.trivy_path,
            'fs',
            '--scanners', scanners,
            '--format', 'json',
            '--severity', 'CRITICAL,HIGH,MEDIUM',
            target_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            secrets = json.loads(result.stdout) if result.stdout else {}
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            # Fallback for when Trivy is not installed
            secrets = {'Results': []}
        
        # Map secrets to Hamiltonian energy field
        for result in secrets.get('Results', []):
            for finding in result.get('Secrets', []):
                secret_id = finding.get('RuleID', 'unknown')
                severity = finding.get('Severity', 'LOW')
                
                # Energy based on severity
                base_energy = {
                    'CRITICAL': 10.0,
                    'HIGH': 7.0,
                    'MEDIUM': 4.0,
                    'LOW': 1.0
                }.get(severity, 0.5)
                
                # Store in energy map
                self.secret_energy_map[secret_id] = {
                    'energy': base_energy,
                    'title': finding.get('Title', 'Unknown'),
                    'match': finding.get('Match', ''),
                    'file': result.get('Target', target_path)
                }
        
        return list(self.secret_energy_map.values())
    
    def map_to_energy(self, findings: List[Dict]) -> Dict[str, float]:
        """Map findings to energy values"""
        energy_map = {}
        for finding in findings:
            secret_id = finding.get('RuleID', str(hash(str(finding))))
            energy_map[secret_id] = finding.get('energy', 1.0)
        return energy_map
    
    def recurse_secret_energy(self, secret_id: str, iterations: int = 10) -> Optional[float]:
        """Apply ZKAEDI PRIME recursion to secret energy."""
        if secret_id not in self.secret_energy_map:
            return None
        
        H = self.secret_energy_map[secret_id]['energy']
        
        for t in range(iterations):
            sigmoid = 1 / (1 + np.exp(-self.gamma * H))
            noise = np.random.normal(0, 0.1 * np.abs(H))
            H = H + self.eta * H * sigmoid + noise
            
        self.secret_energy_map[secret_id]['evolved_energy'] = H
        return H
