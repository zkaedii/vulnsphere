import React, { useState } from 'react'
import {
  Shield,
  AlertTriangle,
  Activity,
  Cpu,
  Database,
  Server,
  Box,
  Radio,
  Zap,
  Eye,
  EyeOff,
  Play,
  Pause,
  RotateCcw,
  Settings,
  Layers,
  Target
} from 'lucide-react'

// Node type icons
const nodeIcons = {
  mainframe: Cpu,
  server: Server,
  database: Database,
  container: Box,
  vm: Layers,
  iot: Radio,
  firewall: Shield
}

// Severity colors
const severityColors = {
  critical: '#ff0000',
  high: '#ff8800',
  medium: '#ffff00',
  low: '#00ff00'
}

function ControlPanel({
  vulns = [],
  ws,
  selectedNode,
  nodes = [],
  onToggleEnergyField,
  onToggleMoat,
  showEnergyField = true,
  showMoat = true,
  chaosMode = false
}) {
  const [activeTab, setActiveTab] = useState('vulns')
  const [suppressingId, setSuppressingId] = useState(null)

  const handleSuppress = async (vulnId, method) => {
    setSuppressingId(vulnId)

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'suppress',
        vulnId,
        method
      }))
    }

    // Simulate suppression delay
    setTimeout(() => setSuppressingId(null), 2000)
  }

  const selectedNodeData = nodes.find(n => n.id === selectedNode)
  const nodeVulns = vulns.filter(v => v.nodeId === selectedNode)

  // Stats
  const criticalCount = vulns.filter(v => v.severity === 'critical').length
  const highCount = vulns.filter(v => v.severity === 'high').length
  const mediumCount = vulns.filter(v => v.severity === 'medium').length

  return (
    <div className="control-panel">
      {/* Header */}
      <div className="panel-header">
        <div className="panel-title">
          <Shield className="panel-icon" />
          <h2>VulnSphere Control</h2>
        </div>
        <div className={`status-indicator ${chaosMode ? 'danger' : 'safe'}`}>
          <Activity className="status-icon" />
          <span>{chaosMode ? 'THREAT DETECTED' : 'MONITORING'}</span>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="stats-bar">
        <div className="stat-item critical">
          <span className="stat-value">{criticalCount}</span>
          <span className="stat-label">Critical</span>
        </div>
        <div className="stat-item high">
          <span className="stat-value">{highCount}</span>
          <span className="stat-label">High</span>
        </div>
        <div className="stat-item medium">
          <span className="stat-value">{mediumCount}</span>
          <span className="stat-label">Medium</span>
        </div>
        <div className="stat-item total">
          <span className="stat-value">{vulns.length}</span>
          <span className="stat-label">Total</span>
        </div>
      </div>

      {/* View Controls */}
      <div className="view-controls">
        <button
          className={`view-toggle ${showEnergyField ? 'active' : ''}`}
          onClick={onToggleEnergyField}
          title="Toggle Energy Field"
        >
          <Zap size={16} />
          <span>Energy Field</span>
        </button>
        <button
          className={`view-toggle ${showMoat ? 'active' : ''}`}
          onClick={onToggleMoat}
          title="Toggle Zero-Trust Moat"
        >
          <Target size={16} />
          <span>Security Moat</span>
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="tab-nav">
        <button
          className={`tab-btn ${activeTab === 'vulns' ? 'active' : ''}`}
          onClick={() => setActiveTab('vulns')}
        >
          <AlertTriangle size={14} />
          Vulnerabilities
        </button>
        <button
          className={`tab-btn ${activeTab === 'node' ? 'active' : ''}`}
          onClick={() => setActiveTab('node')}
        >
          <Cpu size={14} />
          Node Details
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'vulns' && (
          <div className="vulns-list">
            {vulns.length === 0 ? (
              <div className="empty-state">
                <Shield size={48} />
                <p>No vulnerabilities detected</p>
                <span>System is secure</span>
              </div>
            ) : (
              vulns.map((vuln, idx) => (
                <div
                  key={idx}
                  className={`vuln-item ${vuln.severity} ${suppressingId === vuln.id ? 'suppressing' : ''}`}
                >
                  <div className="vuln-header">
                    <div className="vuln-info">
                      <span className="vuln-cve">{vuln.cve || 'CVE-UNKNOWN'}</span>
                      <span className="vuln-node">{vuln.nodeId}</span>
                    </div>
                    <span
                      className="severity-badge"
                      style={{ backgroundColor: severityColors[vuln.severity] }}
                    >
                      {vuln.severity?.toUpperCase()}
                    </span>
                  </div>

                  {vuln.description && (
                    <p className="vuln-desc">{vuln.description}</p>
                  )}

                  <div className="vuln-meta">
                    {vuln.energy && (
                      <span className="vuln-energy">
                        <Zap size={12} />
                        Energy: {vuln.energy.toFixed(2)}
                      </span>
                    )}
                    {vuln.timestamp && (
                      <span className="vuln-time">
                        {new Date(vuln.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>

                  <div className="vuln-actions">
                    <button
                      onClick={() => handleSuppress(vuln.id, 'quarantine')}
                      disabled={suppressingId === vuln.id}
                      className="action-btn quarantine"
                    >
                      <Shield size={14} />
                      Quarantine
                    </button>
                    <button
                      onClick={() => handleSuppress(vuln.id, 'autopatch')}
                      disabled={suppressingId === vuln.id}
                      className="action-btn patch"
                    >
                      <Settings size={14} />
                      Auto-Patch
                    </button>
                    <button
                      onClick={() => handleSuppress(vuln.id, 'ebpf')}
                      disabled={suppressingId === vuln.id}
                      className="action-btn ebpf"
                    >
                      <Zap size={14} />
                      eBPF Shield
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'node' && (
          <div className="node-details">
            {selectedNodeData ? (
              <>
                <div className="node-header">
                  {(() => {
                    const Icon = nodeIcons[selectedNodeData.type] || Server
                    return <Icon size={32} className="node-icon" />
                  })()}
                  <div className="node-title">
                    <h3>{selectedNodeData.id}</h3>
                    <span className="node-type-badge">
                      {selectedNodeData.type?.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="node-info-grid">
                  <div className="info-item">
                    <span className="info-label">Position</span>
                    <span className="info-value">
                      [{selectedNodeData.position?.join(', ')}]
                    </span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Status</span>
                    <span className={`info-value ${nodeVulns.length > 0 ? 'vulnerable' : 'secure'}`}>
                      {nodeVulns.length > 0 ? 'VULNERABLE' : 'SECURE'}
                    </span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Vulnerabilities</span>
                    <span className="info-value">{nodeVulns.length}</span>
                  </div>
                  {selectedNodeData.energy !== undefined && (
                    <div className="info-item">
                      <span className="info-label">Energy Level</span>
                      <span className="info-value">
                        {selectedNodeData.energy.toFixed(3)}
                      </span>
                    </div>
                  )}
                </div>

                {nodeVulns.length > 0 && (
                  <div className="node-vulns">
                    <h4>Node Vulnerabilities</h4>
                    {nodeVulns.map((vuln, idx) => (
                      <div key={idx} className="mini-vuln-item">
                        <span className="mini-cve">{vuln.cve || 'Unknown'}</span>
                        <span
                          className="mini-severity"
                          style={{ color: severityColors[vuln.severity] }}
                        >
                          {vuln.severity}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="node-actions">
                  <button className="node-action-btn scan">
                    <Eye size={14} />
                    Deep Scan
                  </button>
                  <button className="node-action-btn isolate">
                    <Shield size={14} />
                    Isolate Node
                  </button>
                </div>
              </>
            ) : (
              <div className="empty-state">
                <Target size={48} />
                <p>No node selected</p>
                <span>Click a node in the 3D view to see details</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="legend">
        <h4>Node Types</h4>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#ff6600' }} />
            <span>Mainframe</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#00ff88' }} />
            <span>Server</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#ff00aa' }} />
            <span>Database</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#00aaff' }} />
            <span>Container</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#aa66ff' }} />
            <span>VM</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#ffff00' }} />
            <span>IoT</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ background: '#00ffff' }} />
            <span>Firewall</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ControlPanel
