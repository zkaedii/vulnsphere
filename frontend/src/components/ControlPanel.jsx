import React from 'react'

function ControlPanel({ vulns, ws }) {
  const handleSuppress = (vulnId, method) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'suppress',
        vulnId,
        method
      }))
    }
  }

  return (
    <div className="control-panel">
      <h2>🔱 VulnSphere Control</h2>
      
      <div className="vulns-list">
        {vulns.map((vuln, idx) => (
          <div key={idx} className="vuln-item">
            <div className="vuln-header">
              <span className="vuln-cve">{vuln.cve || 'Unknown CVE'}</span>
              <span className={`severity-badge ${vuln.severity}`}>
                {vuln.severity}
              </span>
            </div>
            <div className="vuln-actions">
              <button onClick={() => handleSuppress(vuln.id, 'quarantine')}>
                🛡️ Quarantine
              </button>
              <button onClick={() => handleSuppress(vuln.id, 'autopatch')}>
                🔧 Auto-Patch
              </button>
              <button onClick={() => handleSuppress(vuln.id, 'ebpf')}>
                ⚡ eBPF Shield
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ControlPanel
