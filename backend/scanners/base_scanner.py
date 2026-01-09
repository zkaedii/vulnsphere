"""
Base Scanner Interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScanner(ABC):
    """Base class for all security scanners"""
    
    @abstractmethod
    async def scan(self, target: str) -> List[Dict]:
        """
        Perform security scan on target.
        
        Args:
            target: Target to scan (IP, URL, path, etc.)
        
        Returns:
            List of vulnerability findings
        """
        pass
    
    @abstractmethod
    def map_to_energy(self, findings: List[Dict]) -> Dict[str, float]:
        """
        Map scan findings to Hamiltonian energy values.
        
        Args:
            findings: List of vulnerability findings
        
        Returns:
            Dict mapping node IDs to energy values
        """
        pass
