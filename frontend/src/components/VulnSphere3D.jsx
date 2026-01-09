import React, { useRef, useEffect } from 'react'
import * as THREE from 'three'

class VulnSphere {
  constructor(container) {
    this.scene = new THREE.Scene()
    this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    this.renderer = new THREE.WebGLRenderer({ antialias: true })
    this.renderer.setSize(window.innerWidth, window.innerHeight)
    container.appendChild(this.renderer.domElement)

    // Orbit controls would be added here
    this.camera.position.set(0, 50, 100)

    this.nodes = []
    this.edges = []
    this.vulnParticles = new THREE.Group()
    this.scene.add(this.vulnParticles)

    this.initLighting()
    this.animate()
  }

  initLighting() {
    const ambientLight = new THREE.AmbientLight(0x404040, 2)
    this.scene.add(ambientLight)

    const pointLight = new THREE.PointLight(0x00ffff, 1, 100)
    pointLight.position.set(10, 10, 10)
    this.scene.add(pointLight)
  }

  addNode(id, position, type = 'server') {
    const geometry = new THREE.SphereGeometry(2, 32, 32)
    const material = new THREE.MeshStandardMaterial({
      color: type === 'server' ? 0x00ff00 : 0x0088ff,
      emissive: 0x002200,
      metalness: 0.5,
      roughness: 0.5
    })
    const node = new THREE.Mesh(geometry, material)
    node.position.set(...position)
    node.userData = { id, type, vulns: [] }
    
    this.scene.add(node)
    this.nodes.push(node)
    return node
  }

  addVulnerability(nodeId, cve, severity) {
    const node = this.nodes.find(n => n.userData.id === nodeId)
    if (!node) return

    node.userData.vulns.push({ cve, severity })

    const color = severity === 'critical' ? 0xff0000 : 
                  severity === 'high' ? 0xff8800 : 0xffff00
    
    const vulnGeometry = new THREE.SphereGeometry(0.5, 16, 16)
    const vulnMaterial = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.8
    })
    const vulnOrb = new THREE.Mesh(vulnGeometry, vulnMaterial)
    vulnOrb.position.copy(node.position)
    vulnOrb.position.y += 3
    vulnOrb.userData = { pulse: 0, cve }

    this.vulnParticles.add(vulnOrb)
  }

  animate() {
    requestAnimationFrame(() => this.animate())

    // Pulse vulnerabilities
    this.vulnParticles.children.forEach(orb => {
      orb.userData.pulse += 0.05
      orb.scale.setScalar(1 + 0.2 * Math.sin(orb.userData.pulse))
    })

    this.renderer.render(this.scene, this.camera)
  }
}

function VulnSphere3D({ vulns }) {
  const containerRef = useRef(null)
  const vulnsphereRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    vulnsphereRef.current = new VulnSphere(containerRef.current)

    // Add some demo nodes
    vulnsphereRef.current.addNode('node1', [0, 0, 0])
    vulnsphereRef.current.addNode('node2', [20, 0, 0])
    vulnsphereRef.current.addNode('node3', [0, 20, 0])

    return () => {
      if (vulnsphereRef.current && containerRef.current) {
        containerRef.current.removeChild(vulnsphereRef.current.renderer.domElement)
      }
    }
  }, [])

  useEffect(() => {
    if (!vulnsphereRef.current) return

    vulns.forEach(vuln => {
      vulnsphereRef.current.addVulnerability(
        vuln.nodeId,
        vuln.cve,
        vuln.severity
      )
    })
  }, [vulns])

  return (
    <div 
      ref={containerRef} 
      className="vulnsphere-3d"
      style={{ width: '100%', height: '100vh' }}
    />
  )
}

export default VulnSphere3D
