import React, { useState, useEffect } from 'react'
import VulnSphere3D from './components/VulnSphere3D'
import ControlPanel from './components/ControlPanel'
import './styles/main.css'

function App() {
  const [vulns, setVulns] = useState([])
  const [chaosMode, setChaosMode] = useState(false)
  const [ws, setWs] = useState(null)

  useEffect(() => {
    // WebSocket connection
    const websocket = new WebSocket('ws://localhost:8000/ws')
    
    websocket.onopen = () => {
      console.log('WebSocket connected')
      setWs(websocket)
    }
    
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'vuln_detected') {
        setVulns(prev => [...prev, data])
      } else if (data.type === 'chaos_mode') {
        setChaosMode(true)
      }
    }
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    websocket.onclose = () => {
      console.log('WebSocket disconnected')
      setWs(null)
    }
    
    return () => {
      websocket.close()
    }
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <h1>🔱 VulnSphere PRIME</h1>
        <p>Fractal Security Intelligence Platform</p>
        {chaosMode && (
          <div className="chaos-badge">
            ⚠️ CHAOS MODE ACTIVE
          </div>
        )}
      </header>
      
      <div className="app-content">
        <VulnSphere3D vulns={vulns} />
        <ControlPanel vulns={vulns} ws={ws} />
      </div>
    </div>
  )
}

export default App
