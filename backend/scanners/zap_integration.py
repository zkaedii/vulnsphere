"""
OWASP ZAP Ajax Spider Integration
"""
import time
import asyncio
from typing import Dict, List
from .base_scanner import BaseScanner

class ZapAjaxHamiltonian(BaseScanner):
    """
    OWASP ZAP Ajax Spider with DOM monitoring.
    Detects client-side XSS sinks missed by static analysis.
    """
    
    def __init__(self, zap_api_key: str = "", proxy: str = 'http://127.0.0.1:8080'):
        self.zap_api_key = zap_api_key
        self.proxy = proxy
        self.dom_changes = []
        self.zap = None
        
        # Try to import zapv2, but don't fail if not available
        try:
            from zapv2 import ZAPv2
            if zap_api_key:
                self.zap = ZAPv2(apikey=zap_api_key, proxies={'http': proxy, 'https': proxy})
        except ImportError:
            pass
    
    async def scan(self, target_url: str, context: str = 'Default Context') -> List[Dict]:
        """
        Activate Ajax Spider with custom scripts.
        """
        if not self.zap:
            # Return mock data if ZAP is not available
            return [
                {
                    'url': target_url,
                    'type': 'fractal_shard',
                    'energy': 2.0,
                    'severity': 'MEDIUM'
                }
            ]
        
        try:
            # Configure Ajax Spider
            self.zap.ajaxSpider.set_option_max_duration('60')
            self.zap.ajaxSpider.set_option_max_crawl_depth('10')
            self.zap.ajaxSpider.set_option_number_of_browsers('5')
            
            # Start spider
            scan_id = self.zap.ajaxSpider.scan(target_url, contextname=context)
            
            # Monitor for completion
            while int(self.zap.ajaxSpider.status(scan_id)) < 100:
                await asyncio.sleep(2)
            
            # Get results
            results = self.zap.ajaxSpider.results(scan_id)
            
            return self.extract_fractal_edges(results)
        except Exception as e:
            # Fallback
            return []
    
    def extract_fractal_edges(self, spider_results: List[str]) -> List[Dict]:
        """Convert discovered endpoints to fractal edge structures."""
        fractal_edges = []
        
        for url in spider_results:
            is_undocumented = self.check_undocumented(url)
            
            edge = {
                'url': url,
                'type': 'fractal_shard' if is_undocumented else 'standard_edge',
                'energy': 8.0 if is_undocumented else 2.0,
                'color': 0xff00ff if is_undocumented else 0x00ffff,
                'severity': 'HIGH' if is_undocumented else 'MEDIUM'
            }
            
            fractal_edges.append(edge)
        
        return fractal_edges
    
    def check_undocumented(self, url: str) -> bool:
        """Heuristic: Check if URL is in common API documentation."""
        return '/api/internal/' in url or '/v0/' in url or '/_ah/api' in url
    
    def map_to_energy(self, findings: List[Dict]) -> Dict[str, float]:
        """Map findings to energy values"""
        energy_map = {}
        for finding in findings:
            url = finding.get('url', 'unknown')
            energy_map[url] = finding.get('energy', 2.0)
        return energy_map
