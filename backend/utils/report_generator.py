"""
Report Generation for VulnSphere PRIME

Generates vulnerability reports in multiple formats:
- HTML (styled, interactive)
- PDF (via HTML conversion)
- JSON (machine-readable)
- Markdown (documentation-friendly)
"""

import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate vulnerability scan reports in multiple formats"""

    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"

    def generate_html_report(
        self,
        scan_result: Dict[str, Any],
        network_info: Dict[str, Any] = None,
        include_charts: bool = True,
    ) -> str:
        """
        Generate HTML vulnerability report.

        Args:
            scan_result: Scan results from ZKAEDI engine
            network_info: Optional network metadata
            include_charts: Include Chart.js visualizations

        Returns:
            HTML string
        """
        vulnerabilities = scan_result.get("vulnerabilities", [])
        metrics = scan_result.get("performance_metrics", {})

        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for vuln in vulnerabilities:
            sev = vuln.get("severity", "medium").lower()
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VulnSphere PRIME - Vulnerability Report</title>
    <style>
        :root {{
            --primary: #00ffff;
            --danger: #ff4444;
            --warning: #ffaa00;
            --success: #44ff44;
            --bg-dark: #0a0a1a;
            --bg-card: #1a1a2e;
            --text: #e0e0e0;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-dark);
            color: var(--text);
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 30px;
        }}
        h1 {{
            color: var(--primary);
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .subtitle {{ color: #888; font-size: 1.1em; }}
        .timestamp {{ color: #666; margin-top: 10px; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: var(--bg-card);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #333;
        }}
        .summary-card h3 {{ color: #888; font-size: 0.9em; margin-bottom: 10px; }}
        .summary-card .value {{ font-size: 2em; font-weight: bold; }}
        .critical {{ color: var(--danger); }}
        .high {{ color: #ff8800; }}
        .medium {{ color: var(--warning); }}
        .low {{ color: var(--success); }}
        .section {{
            background: var(--bg-card);
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #333;
        }}
        .section h2 {{
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }}
        .vuln-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .vuln-table th, .vuln-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        .vuln-table th {{ color: var(--primary); }}
        .vuln-table tr:hover {{ background: rgba(0, 255, 255, 0.05); }}
        .severity-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .severity-badge.critical {{ background: rgba(255, 68, 68, 0.2); color: var(--danger); }}
        .severity-badge.high {{ background: rgba(255, 136, 0, 0.2); color: #ff8800; }}
        .severity-badge.medium {{ background: rgba(255, 170, 0, 0.2); color: var(--warning); }}
        .severity-badge.low {{ background: rgba(68, 255, 68, 0.2); color: var(--success); }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .metric {{
            background: rgba(0, 255, 255, 0.05);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-label {{ color: #888; font-size: 0.85em; }}
        .metric-value {{ font-size: 1.4em; color: var(--primary); margin-top: 5px; }}
        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            border-top: 1px solid #333;
            margin-top: 30px;
        }}
        @media print {{
            body {{ background: white; color: black; }}
            .section {{ border: 1px solid #ddd; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>VulnSphere PRIME</h1>
            <p class="subtitle">Vulnerability Assessment Report</p>
            <p class="timestamp">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </header>

        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Vulnerabilities</h3>
                <div class="value">{len(vulnerabilities)}</div>
            </div>
            <div class="summary-card">
                <h3>Critical</h3>
                <div class="value critical">{severity_counts['critical']}</div>
            </div>
            <div class="summary-card">
                <h3>High</h3>
                <div class="value high">{severity_counts['high']}</div>
            </div>
            <div class="summary-card">
                <h3>Medium</h3>
                <div class="value medium">{severity_counts['medium']}</div>
            </div>
            <div class="summary-card">
                <h3>Speedup</h3>
                <div class="value" style="color: var(--primary);">{metrics.get('speedup_factor', 1):.1f}x</div>
            </div>
        </div>

        <div class="section">
            <h2>Performance Metrics</h2>
            <div class="metrics-grid">
                <div class="metric">
                    <div class="metric-label">Iterations</div>
                    <div class="metric-value">{metrics.get('total_iterations', 'N/A')}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Iterations Saved</div>
                    <div class="metric-value">{metrics.get('iterations_saved', 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Chaos Boosts</div>
                    <div class="metric-value">{metrics.get('chaos_boosts_triggered', 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Avg Eta</div>
                    <div class="metric-value">{metrics.get('avg_eta', 0):.3f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Max Energy</div>
                    <div class="metric-value">{metrics.get('max_energy_peak', 0):.2f}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Vulnerability Details</h2>
            <table class="vuln-table">
                <thead>
                    <tr>
                        <th>Node ID</th>
                        <th>Severity</th>
                        <th>Energy</th>
                        <th>Risk Score</th>
                        <th>Connections</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(self._vuln_row(v) for v in vulnerabilities[:50])}
                </tbody>
            </table>
            {f'<p style="color: #888; margin-top: 15px;">Showing 50 of {len(vulnerabilities)} vulnerabilities</p>' if len(vulnerabilities) > 50 else ''}
        </div>

        <footer>
            <p>Generated by VulnSphere PRIME - Fractal Security Intelligence Platform</p>
            <p>ZKAEDI PRIME Engine v1.0.0</p>
        </footer>
    </div>
</body>
</html>"""

        return html

    def _vuln_row(self, vuln: Dict) -> str:
        """Generate HTML table row for vulnerability"""
        severity = vuln.get("severity", "medium").lower()
        neighbors = vuln.get("neighbors", [])
        return f"""
        <tr>
            <td>{vuln.get('node_id', 'Unknown')}</td>
            <td><span class="severity-badge {severity}">{severity}</span></td>
            <td>{vuln.get('energy', 0):.4f}</td>
            <td>{vuln.get('risk_score', 0)}</td>
            <td>{len(neighbors)}</td>
        </tr>"""

    def generate_json_report(
        self, scan_result: Dict[str, Any], network_info: Dict[str, Any] = None
    ) -> str:
        """Generate JSON report"""
        report = {
            "report_type": "vulnerability_assessment",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "generator": "VulnSphere PRIME v1.0.0",
            "summary": {
                "total_vulnerabilities": len(scan_result.get("vulnerabilities", [])),
                "severity_breakdown": self._count_severities(
                    scan_result.get("vulnerabilities", [])
                ),
                "converged": scan_result.get("converged", False),
                "speedup_factor": scan_result.get("performance_metrics", {}).get(
                    "speedup_factor", 1
                ),
            },
            "performance_metrics": scan_result.get("performance_metrics", {}),
            "vulnerabilities": scan_result.get("vulnerabilities", []),
            "stability_log": scan_result.get("stability_log", [])[
                -10:
            ],  # Last 10 entries
            "network_info": network_info,
        }
        return json.dumps(report, indent=2, default=str)

    def generate_markdown_report(
        self, scan_result: Dict[str, Any], network_info: Dict[str, Any] = None
    ) -> str:
        """Generate Markdown report"""
        vulnerabilities = scan_result.get("vulnerabilities", [])
        metrics = scan_result.get("performance_metrics", {})
        severity_counts = self._count_severities(vulnerabilities)

        md = f"""# VulnSphere PRIME - Vulnerability Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Vulnerabilities | {len(vulnerabilities)} |
| Critical | {severity_counts.get('critical', 0)} |
| High | {severity_counts.get('high', 0)} |
| Medium | {severity_counts.get('medium', 0)} |
| Speedup Factor | {metrics.get('speedup_factor', 1):.2f}x |
| Converged | {'Yes' if scan_result.get('converged') else 'No'} |

## Performance Metrics

- **Iterations:** {metrics.get('total_iterations', 'N/A')}
- **Iterations Saved:** {metrics.get('iterations_saved', 0)}
- **Chaos Boosts:** {metrics.get('chaos_boosts_triggered', 0)}
- **Average Eta:** {metrics.get('avg_eta', 0):.4f}
- **Max Energy Peak:** {metrics.get('max_energy_peak', 0):.4f}

## Top Vulnerabilities

| Node ID | Severity | Energy | Risk Score |
|---------|----------|--------|------------|
"""
        for vuln in vulnerabilities[:20]:
            md += f"| {vuln.get('node_id', 'Unknown')} | {vuln.get('severity', 'medium').upper()} | {vuln.get('energy', 0):.4f} | {vuln.get('risk_score', 0)} |\n"

        md += f"""
## Recommendations

1. **Critical vulnerabilities** should be addressed immediately
2. **High severity** issues should be prioritized in the next sprint
3. Review network topology for high-energy nodes
4. Consider implementing zero-trust segmentation for vulnerable nodes

---

*Generated by VulnSphere PRIME - Fractal Security Intelligence Platform*
"""
        return md

    def _count_severities(self, vulnerabilities: List[Dict]) -> Dict[str, int]:
        """Count vulnerabilities by severity"""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for vuln in vulnerabilities:
            sev = vuln.get("severity", "medium").lower()
            counts[sev] = counts.get(sev, 0) + 1
        return counts

    def save_report(self, content: str, filepath: str, format: str = "html") -> str:
        """Save report to file"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Report saved to {path}")
        return str(path)
