import React, { useState, useEffect, useCallback } from 'react'
import VulnSphere3D from './components/VulnSphere3D'
import ControlPanel from './components/ControlPanel'
import './styles/main.css'

// Demo vulnerability data for testing
const DEMO_VULNS = [
  {
    id: 'vuln-001',
    nodeId: 'db-primary',
    cve: 'CVE-2024-21762',
    severity: 'critical',
    description: 'FortiOS SSL VPN buffer overflow vulnerability',
    energy: 8.5,
    timestamp: new Date().toISOString()
  },
  {
    id: 'vuln-002',
    nodeId: 'app-server-01',
    cve: 'CVE-2024-3400',
    severity: 'critical',
    description: 'PAN-OS GlobalProtect command injection',
    energy: 9.2,
    timestamp: new Date().toISOString()
  },
  {
    id: 'vuln-003',
    nodeId: 'k8s-pod-01',
    cve: 'CVE-2024-1086',
    severity: 'high',
    description: 'Linux kernel nf_tables use-after-free',
    energy: 7.1,
    timestamp: new Date().toISOString()
  },
  {
    id: 'vuln-004',
    nodeId: 'vm-azure-01',
    cve: 'CVE-2024-27198',
    severity: 'high',
    description: 'JetBrains TeamCity authentication bypass',
    energy: 6.8,
    timestamp: new Date().toISOString()
  },
  {
    id: 'vuln-005',
    nodeId: 'iot-sensor-02',
    cve: 'CVE-2024-0204',
    severity: 'medium',
    description: 'Fortra GoAnywhere MFT auth bypass',
    energy: 5.2,
    timestamp: new Date().toISOString()
  }
]

// Demo nodes data
const DEMO_NODES = [
  { id: 'mainframe-01', position: [0, 0, 0], type: 'mainframe' },
  { id: 'db-primary', position: [20, 0, 0], type: 'database' },
  { id: 'db-replica', position: [-20, 0, 0], type: 'database' },
  { id: 'firewall-01', position: [0, 0, 20], type: 'firewall' },
  { id: 'firewall-02', position: [0, 0, -20], type: 'firewall' },
  { id: 'app-server-01', position: [35, 5, 15], type: 'server' },
  { id: 'app-server-02', position: [35, 5, -15], type: 'server' },
  { id: 'app-server-03', position: [-35, 5, 15], type: 'server' },
  { id: 'app-server-04', position: [-35, 5, -15], type: 'server' },
  { id: 'k8s-pod-01', position: [50, 0, 0], type: 'container' },
  { id: 'k8s-pod-02', position: [-50, 0, 0], type: 'container' },
  { id: 'k8s-pod-03', position: [0, 0, 50], type: 'container' },
  { id: 'k8s-pod-04', position: [0, 0, -50], type: 'container' },
  { id: 'vm-azure-01', position: [40, 0, 40], type: 'vm' },
  { id: 'vm-azure-02', position: [-40, 0, 40], type: 'vm' },
  { id: 'vm-aws-01', position: [40, 0, -40], type: 'vm' },
  { id: 'vm-aws-02', position: [-40, 0, -40], type: 'vm' },
  { id: 'iot-sensor-01', position: [60, -5, 30], type: 'iot' },
  { id: 'iot-sensor-02', position: [-60, -5, 30], type: 'iot' },
  { id: 'iot-sensor-03', position: [60, -5, -30], type: 'iot' },
  { id: 'iot-sensor-04', position: [-60, -5, -30], type: 'iot' }
]

function App() {
  const [vulns, setVulns] = useState(DEMO_VULNS)
  const [chaosMode, setChaosMode] = useState(false)
  const [ws, setWs] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const [showEnergyField, setShowEnergyField] = useState(true)
  const [showMoat, setShowMoat] = useState(true)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const websocket = new WebSocket('ws://localhost:8000/ws')

        websocket.onopen = () => {
          console.log('WebSocket connected')
          setWs(websocket)
          setConnectionStatus('connected')
        }

        websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)

            if (data.type === 'vuln_detected') {
              setVulns(prev => [...prev, {
                id: data.id || `vuln-${Date.now()}`,
                nodeId: data.nodeId,
                cve: data.cve,
                severity: data.severity,
                description: data.description,
                energy: data.energy,
                timestamp: data.timestamp || new Date().toISOString()
              }])
            } else if (data.type === 'chaos_mode') {
              setChaosMode(true)
              setTimeout(() => setChaosMode(false), 10000) // Reset after 10s
            } else if (data.type === 'suppression_complete') {
              setVulns(prev => prev.filter(v => v.id !== data.vulnId))
            }
          } catch (err) {
            console.error('Error parsing WebSocket message:', err)
          }
        }

        websocket.onerror = (error) => {
          console.error('WebSocket error:', error)
          setConnectionStatus('error')
        }

        websocket.onclose = () => {
          console.log('WebSocket disconnected')
          setWs(null)
          setConnectionStatus('disconnected')
        }

        return websocket
      } catch (err) {
        console.error('Failed to create WebSocket:', err)
        setConnectionStatus('error')
        return null
      }
    }

    const websocket = connectWebSocket()

    return () => {
      if (websocket) {
        websocket.close()
      }
    }
  }, [])

  // Handle node selection from 3D view
  const handleNodeSelect = useCallback((nodeId) => {
    setSelectedNode(prev => prev === nodeId ? null : nodeId)
  }, [])

  // Toggle view controls
  const handleToggleEnergyField = useCallback(() => {
    setShowEnergyField(prev => !prev)
  }, [])

  const handleToggleMoat = useCallback(() => {
    setShowMoat(prev => !prev)
  }, [])

  // Trigger demo chaos mode
  const triggerChaosDemo = useCallback(() => {
    setChaosMode(true)

    // Add some demo attack vulnerabilities
    const newVuln = {
      id: `vuln-attack-${Date.now()}`,
      nodeId: DEMO_NODES[Math.floor(Math.random() * DEMO_NODES.length)].id,
      cve: 'CVE-2024-ATTACK',
      severity: 'critical',
      description: 'Active exploitation detected - Hamiltonian anomaly',
      energy: 9.9,
      timestamp: new Date().toISOString()
    }
    setVulns(prev => [...prev, newVuln])

    setTimeout(() => setChaosMode(false), 10000)
  }, [])

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <h1>VulnSphere PRIME</h1>
          <p>Fractal Security Intelligence Platform</p>
        </div>
        <div className="header-right">
          <div className={`connection-status ${connectionStatus}`}>
            <span className="status-dot" />
            <span className="status-text">
              {connectionStatus === 'connected' ? 'Live' :
               connectionStatus === 'error' ? 'Error' : 'Offline'}
            </span>
          </div>
          <button
            className="chaos-trigger"
            onClick={triggerChaosDemo}
            disabled={chaosMode}
          >
            Simulate Attack
          </button>
          {chaosMode && (
            <div className="chaos-badge">
              CHAOS MODE ACTIVE
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="app-content">
        <VulnSphere3D
          vulns={vulns}
          chaosMode={chaosMode}
          showEnergyField={showEnergyField}
          showMoat={showMoat}
          onNodeSelect={handleNodeSelect}
        />
        <ControlPanel
          vulns={vulns}
          ws={ws}
          selectedNode={selectedNode}
          nodes={DEMO_NODES}
          onToggleEnergyField={handleToggleEnergyField}
          onToggleMoat={handleToggleMoat}
          showEnergyField={showEnergyField}
          showMoat={showMoat}
          chaosMode={chaosMode}
        />
      </div>
    </div>
  )
}

export default App
