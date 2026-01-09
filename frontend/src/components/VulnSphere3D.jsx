import React, { useRef, useEffect, useState, useCallback } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'

class VulnSphere {
  constructor(container) {
    this.scene = new THREE.Scene()
    this.scene.background = new THREE.Color(0x0a0a1a)

    this.camera = new THREE.PerspectiveCamera(
      75,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    )
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true
    })
    this.renderer.setSize(container.clientWidth, container.clientHeight)
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(this.renderer.domElement)

    // Orbit controls for camera interaction
    this.controls = new OrbitControls(this.camera, this.renderer.domElement)
    this.controls.enableDamping = true
    this.controls.dampingFactor = 0.05
    this.controls.enableZoom = true
    this.controls.enablePan = true
    this.controls.minDistance = 20
    this.controls.maxDistance = 300
    this.controls.autoRotate = false
    this.controls.autoRotateSpeed = 0.5

    this.camera.position.set(0, 50, 100)
    this.controls.target.set(0, 0, 0)
    this.controls.update()

    this.nodes = []
    this.edges = []
    this.vulnParticles = new THREE.Group()
    this.scene.add(this.vulnParticles)

    // Energy field visualization
    this.energyField = null
    this.energyFieldData = null

    // Raycaster for node selection
    this.raycaster = new THREE.Raycaster()
    this.mouse = new THREE.Vector2()
    this.selectedNode = null
    this.hoveredNode = null

    // Event listeners
    this.container = container
    this.onMouseMove = this.onMouseMove.bind(this)
    this.onClick = this.onClick.bind(this)
    this.onResize = this.onResize.bind(this)

    container.addEventListener('mousemove', this.onMouseMove)
    container.addEventListener('click', this.onClick)
    window.addEventListener('resize', this.onResize)

    this.initLighting()
    this.initGrid()
    this.animate()
  }

  initLighting() {
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0x404060, 1)
    this.scene.add(ambientLight)

    // Point lights for dramatic effect
    const pointLight1 = new THREE.PointLight(0x00ffff, 1, 200)
    pointLight1.position.set(50, 50, 50)
    this.scene.add(pointLight1)

    const pointLight2 = new THREE.PointLight(0xff00ff, 0.5, 200)
    pointLight2.position.set(-50, -50, 50)
    this.scene.add(pointLight2)

    // Directional light for shadows
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.5)
    dirLight.position.set(0, 100, 0)
    this.scene.add(dirLight)
  }

  initGrid() {
    // Add a subtle grid for orientation
    const gridHelper = new THREE.GridHelper(200, 50, 0x222244, 0x111133)
    gridHelper.position.y = -20
    this.scene.add(gridHelper)
  }

  addNode(id, position, type = 'server', energy = 0) {
    const geometry = new THREE.SphereGeometry(2, 32, 32)

    // Color based on type and energy
    let baseColor = type === 'server' ? 0x00ff88 :
                    type === 'database' ? 0x00aaff :
                    type === 'firewall' ? 0xff8800 : 0x0088ff

    const material = new THREE.MeshStandardMaterial({
      color: baseColor,
      emissive: baseColor,
      emissiveIntensity: 0.2 + Math.min(energy * 0.1, 0.5),
      metalness: 0.7,
      roughness: 0.3,
      transparent: true,
      opacity: 0.9
    })

    const node = new THREE.Mesh(geometry, material)
    node.position.set(...position)
    node.userData = { id, type, vulns: [], energy, originalColor: baseColor }

    // Add glow effect
    const glowGeometry = new THREE.SphereGeometry(2.5, 32, 32)
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: baseColor,
      transparent: true,
      opacity: 0.15
    })
    const glow = new THREE.Mesh(glowGeometry, glowMaterial)
    node.add(glow)

    this.scene.add(node)
    this.nodes.push(node)
    return node
  }

  addEdge(fromId, toId) {
    const fromNode = this.nodes.find(n => n.userData.id === fromId)
    const toNode = this.nodes.find(n => n.userData.id === toId)

    if (!fromNode || !toNode) return

    const points = [fromNode.position, toNode.position]
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const material = new THREE.LineBasicMaterial({
      color: 0x334466,
      transparent: true,
      opacity: 0.5
    })
    const line = new THREE.Line(geometry, material)
    line.userData = { from: fromId, to: toId }

    this.scene.add(line)
    this.edges.push(line)
    return line
  }

  addVulnerability(nodeId, cve, severity, energy = 5) {
    const node = this.nodes.find(n => n.userData.id === nodeId)
    if (!node) return

    node.userData.vulns.push({ cve, severity, energy })

    // Update node appearance based on vulnerability count
    const vulnCount = node.userData.vulns.length
    node.material.emissiveIntensity = Math.min(0.2 + vulnCount * 0.15, 0.8)

    // Determine color based on severity
    const color = severity === 'critical' ? 0xff0000 :
                  severity === 'high' ? 0xff8800 :
                  severity === 'medium' ? 0xffff00 : 0x00ff00

    // Create vulnerability orb
    const vulnGeometry = new THREE.SphereGeometry(0.5 + energy * 0.05, 16, 16)
    const vulnMaterial = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.8
    })
    const vulnOrb = new THREE.Mesh(vulnGeometry, vulnMaterial)

    // Position around the node in a spiral
    const angle = vulnCount * 0.8
    const radius = 3 + vulnCount * 0.3
    vulnOrb.position.copy(node.position)
    vulnOrb.position.x += Math.cos(angle) * radius
    vulnOrb.position.y += 2 + Math.sin(angle * 2)
    vulnOrb.position.z += Math.sin(angle) * radius

    vulnOrb.userData = {
      pulse: Math.random() * Math.PI * 2,
      cve,
      severity,
      parentNode: node,
      energy,
      baseScale: 1 + energy * 0.05
    }

    this.vulnParticles.add(vulnOrb)
    return vulnOrb
  }

  updateEnergyField(energyData) {
    this.energyFieldData = energyData

    // Update node colors based on energy
    this.nodes.forEach((node, index) => {
      if (energyData[index] !== undefined) {
        const energy = Math.abs(energyData[index])
        node.userData.energy = energy

        // Color gradient from green (low) to red (high)
        const hue = Math.max(0, 0.33 - energy * 0.033) // Green to Red
        const color = new THREE.Color().setHSL(hue, 1, 0.5)

        node.material.color = color
        node.material.emissive = color
        node.material.emissiveIntensity = 0.2 + Math.min(energy * 0.08, 0.6)
      }
    })
  }

  onMouseMove(event) {
    const rect = this.container.getBoundingClientRect()
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

    // Raycast for hover effects
    this.raycaster.setFromCamera(this.mouse, this.camera)
    const intersects = this.raycaster.intersectObjects(this.nodes)

    // Reset previous hover
    if (this.hoveredNode && this.hoveredNode !== this.selectedNode) {
      this.hoveredNode.scale.setScalar(1)
    }

    if (intersects.length > 0) {
      this.hoveredNode = intersects[0].object
      this.hoveredNode.scale.setScalar(1.2)
      this.container.style.cursor = 'pointer'
    } else {
      this.hoveredNode = null
      this.container.style.cursor = 'grab'
    }
  }

  onClick(event) {
    if (!this.hoveredNode) {
      // Deselect
      if (this.selectedNode) {
        this.selectedNode.scale.setScalar(1)
        this.selectedNode = null
      }
      return
    }

    // Deselect previous
    if (this.selectedNode) {
      this.selectedNode.scale.setScalar(1)
    }

    this.selectedNode = this.hoveredNode
    this.selectedNode.scale.setScalar(1.3)

    // Dispatch custom event for external handlers
    const customEvent = new CustomEvent('nodeSelected', {
      detail: this.selectedNode.userData
    })
    this.container.dispatchEvent(customEvent)
  }

  onResize() {
    const width = this.container.clientWidth
    const height = this.container.clientHeight

    this.camera.aspect = width / height
    this.camera.updateProjectionMatrix()
    this.renderer.setSize(width, height)
  }

  setAutoRotate(enabled) {
    this.controls.autoRotate = enabled
  }

  focusOnNode(nodeId) {
    const node = this.nodes.find(n => n.userData.id === nodeId)
    if (!node) return

    // Animate camera to focus on node
    const targetPosition = node.position.clone()
    targetPosition.z += 30

    this.controls.target.copy(node.position)
    this.camera.position.lerp(targetPosition, 0.1)
  }

  clearAll() {
    // Clear nodes
    this.nodes.forEach(node => this.scene.remove(node))
    this.nodes = []

    // Clear edges
    this.edges.forEach(edge => this.scene.remove(edge))
    this.edges = []

    // Clear vulnerability particles
    while (this.vulnParticles.children.length > 0) {
      this.vulnParticles.remove(this.vulnParticles.children[0])
    }
  }

  animate() {
    requestAnimationFrame(() => this.animate())

    // Update controls
    this.controls.update()

    // Pulse vulnerabilities
    const time = Date.now() * 0.001
    this.vulnParticles.children.forEach(orb => {
      orb.userData.pulse += 0.05
      const scale = orb.userData.baseScale * (1 + 0.2 * Math.sin(orb.userData.pulse))
      orb.scale.setScalar(scale)

      // Subtle floating motion
      orb.position.y += Math.sin(time + orb.userData.pulse) * 0.01
    })

    // Subtle node pulsing
    this.nodes.forEach((node, i) => {
      const pulseIntensity = 0.02 + (node.userData.vulns.length * 0.01)
      node.scale.setScalar(1 + Math.sin(time * 2 + i) * pulseIntensity)
    })

    this.renderer.render(this.scene, this.camera)
  }

  dispose() {
    this.container.removeEventListener('mousemove', this.onMouseMove)
    this.container.removeEventListener('click', this.onClick)
    window.removeEventListener('resize', this.onResize)

    this.controls.dispose()
    this.renderer.dispose()

    if (this.container.contains(this.renderer.domElement)) {
      this.container.removeChild(this.renderer.domElement)
    }
  }
}

function VulnSphere3D({
  vulns = [],
  nodes: nodeData = null,
  edges: edgeData = null,
  energyField = null,
  onNodeSelect = null,
  autoRotate = false
}) {
  const containerRef = useRef(null)
  const vulnsphereRef = useRef(null)
  const [selectedNode, setSelectedNode] = useState(null)

  // Initialize VulnSphere
  useEffect(() => {
    if (!containerRef.current) return

    vulnsphereRef.current = new VulnSphere(containerRef.current)

    // Handle node selection events
    const handleNodeSelect = (event) => {
      setSelectedNode(event.detail)
      if (onNodeSelect) {
        onNodeSelect(event.detail)
      }
    }
    containerRef.current.addEventListener('nodeSelected', handleNodeSelect)

    // Add demo nodes if no data provided
    if (!nodeData) {
      vulnsphereRef.current.addNode('hub', [0, 0, 0], 'server')
      vulnsphereRef.current.addNode('db1', [30, 0, 0], 'database')
      vulnsphereRef.current.addNode('db2', [-30, 0, 0], 'database')
      vulnsphereRef.current.addNode('web1', [0, 0, 30], 'server')
      vulnsphereRef.current.addNode('web2', [0, 0, -30], 'server')
      vulnsphereRef.current.addNode('fw', [0, 30, 0], 'firewall')

      // Add edges
      vulnsphereRef.current.addEdge('hub', 'db1')
      vulnsphereRef.current.addEdge('hub', 'db2')
      vulnsphereRef.current.addEdge('hub', 'web1')
      vulnsphereRef.current.addEdge('hub', 'web2')
      vulnsphereRef.current.addEdge('fw', 'hub')
    }

    return () => {
      if (containerRef.current) {
        containerRef.current.removeEventListener('nodeSelected', handleNodeSelect)
      }
      if (vulnsphereRef.current) {
        vulnsphereRef.current.dispose()
      }
    }
  }, [])

  // Handle node data updates
  useEffect(() => {
    if (!vulnsphereRef.current || !nodeData) return

    vulnsphereRef.current.clearAll()

    nodeData.forEach(node => {
      vulnsphereRef.current.addNode(
        node.id,
        node.position || [
          Math.random() * 100 - 50,
          Math.random() * 50 - 25,
          Math.random() * 100 - 50
        ],
        node.type || 'server',
        node.energy || 0
      )
    })

    if (edgeData) {
      edgeData.forEach(edge => {
        vulnsphereRef.current.addEdge(edge.from, edge.to)
      })
    }
  }, [nodeData, edgeData])

  // Handle vulnerability updates
  useEffect(() => {
    if (!vulnsphereRef.current) return

    vulns.forEach(vuln => {
      vulnsphereRef.current.addVulnerability(
        vuln.nodeId || vuln.node_id,
        vuln.cve,
        vuln.severity,
        vuln.energy || 5
      )
    })
  }, [vulns])

  // Handle energy field updates
  useEffect(() => {
    if (!vulnsphereRef.current || !energyField) return
    vulnsphereRef.current.updateEnergyField(energyField)
  }, [energyField])

  // Handle auto-rotate toggle
  useEffect(() => {
    if (!vulnsphereRef.current) return
    vulnsphereRef.current.setAutoRotate(autoRotate)
  }, [autoRotate])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div
        ref={containerRef}
        className="vulnsphere-3d"
        style={{ width: '100%', height: '100%' }}
      />

      {/* Selected Node Info Panel */}
      {selectedNode && (
        <div style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          background: 'rgba(0, 0, 0, 0.8)',
          color: '#fff',
          padding: '15px',
          borderRadius: '8px',
          minWidth: '200px',
          border: '1px solid #333'
        }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#00ffff' }}>
            {selectedNode.id}
          </h3>
          <p style={{ margin: '5px 0', fontSize: '14px' }}>
            Type: <span style={{ color: '#888' }}>{selectedNode.type}</span>
          </p>
          <p style={{ margin: '5px 0', fontSize: '14px' }}>
            Energy: <span style={{ color: selectedNode.energy > 5 ? '#ff4444' : '#44ff44' }}>
              {selectedNode.energy?.toFixed(2) || '0.00'}
            </span>
          </p>
          <p style={{ margin: '5px 0', fontSize: '14px' }}>
            Vulnerabilities: <span style={{ color: '#ffaa00' }}>
              {selectedNode.vulns?.length || 0}
            </span>
          </p>
          {selectedNode.vulns?.length > 0 && (
            <div style={{ marginTop: '10px', fontSize: '12px' }}>
              {selectedNode.vulns.map((v, i) => (
                <div key={i} style={{
                  padding: '3px 6px',
                  margin: '2px 0',
                  background: v.severity === 'critical' ? '#ff000044' :
                              v.severity === 'high' ? '#ff880044' : '#ffff0044',
                  borderRadius: '3px'
                }}>
                  {v.cve} ({v.severity})
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Controls Help */}
      <div style={{
        position: 'absolute',
        bottom: '10px',
        left: '10px',
        background: 'rgba(0, 0, 0, 0.6)',
        color: '#888',
        padding: '8px 12px',
        borderRadius: '4px',
        fontSize: '12px'
      }}>
        Drag to rotate | Scroll to zoom | Click node to select
      </div>
    </div>
  )
}

export default VulnSphere3D
