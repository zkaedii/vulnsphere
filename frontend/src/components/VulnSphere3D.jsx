import React, { useRef, useMemo, useState, useCallback, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import {
  OrbitControls,
  Stars,
  Html,
  Float,
  MeshDistortMaterial,
  Sphere,
  Box,
  Line,
  Text,
  Environment
} from '@react-three/drei'
import * as THREE from 'three'
import { EffectComposer, Bloom, ChromaticAberration } from '@react-three/postprocessing'

// ============================================
// NETWORK NODE COMPONENT
// ============================================
function NetworkNode({
  id,
  position,
  type = 'server',
  vulnerabilities = [],
  onSelect,
  isSelected,
  energy = 0
}) {
  const meshRef = useRef()
  const glowRef = useRef()
  const [hovered, setHovered] = useState(false)

  // Node colors by type
  const nodeColors = {
    mainframe: '#ff6600',
    server: '#00ff88',
    container: '#00aaff',
    vm: '#aa66ff',
    iot: '#ffff00',
    database: '#ff00aa',
    firewall: '#00ffff'
  }

  const baseColor = nodeColors[type] || '#00ff88'
  const hasVulns = vulnerabilities.length > 0
  const criticalCount = vulnerabilities.filter(v => v.severity === 'critical').length

  // Determine node color based on vulnerability state
  const nodeColor = useMemo(() => {
    if (criticalCount > 0) return '#ff0000'
    if (hasVulns) return '#ff8800'
    return baseColor
  }, [criticalCount, hasVulns, baseColor])

  // Animation
  useFrame((state) => {
    if (meshRef.current) {
      // Subtle floating animation
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 0.5 + id.charCodeAt(0)) * 0.3

      // Pulse when selected or has vulns
      if (isSelected || hasVulns) {
        const scale = 1 + 0.1 * Math.sin(state.clock.elapsedTime * 3)
        meshRef.current.scale.setScalar(scale)
      }
    }

    if (glowRef.current && hasVulns) {
      glowRef.current.material.opacity = 0.3 + 0.2 * Math.sin(state.clock.elapsedTime * 4)
    }
  })

  // Node geometry based on type
  const NodeGeometry = () => {
    const size = type === 'mainframe' ? 3 : type === 'firewall' ? 2.5 : 2

    if (type === 'mainframe' || type === 'database') {
      return <boxGeometry args={[size, size * 1.5, size]} />
    } else if (type === 'firewall') {
      return <octahedronGeometry args={[size, 0]} />
    } else if (type === 'container') {
      return <cylinderGeometry args={[size * 0.8, size * 0.8, size * 1.2, 6]} />
    }
    return <sphereGeometry args={[size, 32, 32]} />
  }

  return (
    <group position={position}>
      {/* Main node mesh */}
      <mesh
        ref={meshRef}
        onClick={(e) => {
          e.stopPropagation()
          onSelect && onSelect(id)
        }}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <NodeGeometry />
        <meshStandardMaterial
          color={nodeColor}
          emissive={nodeColor}
          emissiveIntensity={hovered || isSelected ? 0.8 : 0.3}
          metalness={0.7}
          roughness={0.2}
        />
      </mesh>

      {/* Glow effect for vulnerable nodes */}
      {hasVulns && (
        <mesh ref={glowRef} scale={1.5}>
          <sphereGeometry args={[2.5, 16, 16]} />
          <meshBasicMaterial
            color={criticalCount > 0 ? '#ff0000' : '#ff8800'}
            transparent
            opacity={0.3}
            side={THREE.BackSide}
          />
        </mesh>
      )}

      {/* Selection ring */}
      {isSelected && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[3.5, 4, 32]} />
          <meshBasicMaterial color="#00ffff" transparent opacity={0.8} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Node label */}
      {(hovered || isSelected) && (
        <Html position={[0, 4, 0]} center distanceFactor={20}>
          <div className="node-label">
            <div className="node-id">{id}</div>
            <div className="node-type">{type.toUpperCase()}</div>
            {hasVulns && (
              <div className="node-vulns">
                {vulnerabilities.length} Vulnerabilities
              </div>
            )}
          </div>
        </Html>
      )}

      {/* Vulnerability particles orbiting the node */}
      {vulnerabilities.map((vuln, idx) => (
        <VulnParticle
          key={vuln.cve || idx}
          vuln={vuln}
          index={idx}
          total={vulnerabilities.length}
        />
      ))}
    </group>
  )
}

// ============================================
// VULNERABILITY PARTICLE
// ============================================
function VulnParticle({ vuln, index, total }) {
  const ref = useRef()
  const angle = (index / total) * Math.PI * 2
  const radius = 4

  const color = vuln.severity === 'critical' ? '#ff0000' :
                vuln.severity === 'high' ? '#ff8800' : '#ffff00'

  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.elapsedTime * 0.5 + angle
      ref.current.position.x = Math.cos(t) * radius
      ref.current.position.z = Math.sin(t) * radius
      ref.current.position.y = Math.sin(t * 2) * 1.5

      // Pulsing scale
      const scale = 0.3 + 0.1 * Math.sin(state.clock.elapsedTime * 4)
      ref.current.scale.setScalar(scale)
    }
  })

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[1, 16, 16]} />
      <meshBasicMaterial color={color} transparent opacity={0.9} />
    </mesh>
  )
}

// ============================================
// NETWORK EDGE (CONNECTION)
// ============================================
function NetworkEdge({ start, end, active = false, dataFlow = false }) {
  const lineRef = useRef()
  const particlesRef = useRef()

  const points = useMemo(() => {
    return [new THREE.Vector3(...start), new THREE.Vector3(...end)]
  }, [start, end])

  const color = active ? '#00ffff' : '#004466'

  // Animate data flow particles
  useFrame((state) => {
    if (particlesRef.current && dataFlow) {
      const startVec = points[0]
      const endVec = points[1]

      particlesRef.current.children.forEach((particle, i) => {
        const t = (state.clock.elapsedTime * 0.3 + i * 0.2) % 1
        particle.position.lerpVectors(startVec, endVec, t)
      })
    }
  })

  return (
    <group>
      <Line
        ref={lineRef}
        points={points}
        color={color}
        lineWidth={active ? 2 : 1}
        transparent
        opacity={active ? 0.8 : 0.3}
      />

      {/* Data flow particles */}
      {dataFlow && (
        <group ref={particlesRef}>
          {[0, 1, 2].map(i => (
            <mesh key={i}>
              <sphereGeometry args={[0.3, 8, 8]} />
              <meshBasicMaterial color="#00ffff" transparent opacity={0.8} />
            </mesh>
          ))}
        </group>
      )}
    </group>
  )
}

// ============================================
// ENERGY FIELD (HAMILTONIAN VISUALIZATION)
// ============================================
function EnergyField({ energyData = [], visible = true }) {
  const meshRef = useRef()

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.05

      // Animate vertices for wave effect
      const positions = meshRef.current.geometry.attributes.position
      for (let i = 0; i < positions.count; i++) {
        const x = positions.getX(i)
        const z = positions.getZ(i)
        const wave = Math.sin(x * 0.3 + state.clock.elapsedTime) *
                     Math.cos(z * 0.3 + state.clock.elapsedTime) * 2
        positions.setY(i, wave - 30)
      }
      positions.needsUpdate = true
    }
  })

  if (!visible) return null

  return (
    <mesh ref={meshRef} position={[0, -30, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[200, 200, 50, 50]} />
      <meshStandardMaterial
        color="#003366"
        wireframe
        transparent
        opacity={0.3}
        emissive="#0066aa"
        emissiveIntensity={0.2}
      />
    </mesh>
  )
}

// ============================================
// ZERO TRUST MOAT (SECURITY BARRIER)
// ============================================
function ZeroTrustMoat({ center = [0, 0, 0], radius = 30, active = true }) {
  const meshRef = useRef()
  const shieldRef = useRef()

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.1
    }
    if (shieldRef.current) {
      shieldRef.current.material.opacity = 0.1 + 0.05 * Math.sin(state.clock.elapsedTime * 2)
    }
  })

  if (!active) return null

  return (
    <group position={center}>
      {/* Hexagonal barrier rings */}
      <mesh ref={meshRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[radius, 0.5, 16, 6]} />
        <meshStandardMaterial
          color="#00ffff"
          emissive="#00ffff"
          emissiveIntensity={0.5}
          transparent
          opacity={0.6}
        />
      </mesh>

      {/* Shield dome */}
      <mesh ref={shieldRef}>
        <sphereGeometry args={[radius * 1.2, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshBasicMaterial
          color="#00ffff"
          transparent
          opacity={0.1}
          side={THREE.DoubleSide}
          wireframe
        />
      </mesh>

      {/* Inner energy ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[radius - 2, radius, 64]} />
        <meshBasicMaterial
          color="#004488"
          transparent
          opacity={0.2}
          side={THREE.DoubleSide}
        />
      </mesh>
    </group>
  )
}

// ============================================
// ATTACK PROBE VISUALIZATION
// ============================================
function AttackProbe({ source, target, active = true }) {
  const ref = useRef()
  const trailRef = useRef()

  useFrame((state) => {
    if (ref.current && active) {
      const t = (state.clock.elapsedTime * 0.5) % 1
      const startVec = new THREE.Vector3(...source)
      const targetVec = new THREE.Vector3(...target)
      ref.current.position.lerpVectors(startVec, targetVec, t)

      // Spin effect
      ref.current.rotation.x = state.clock.elapsedTime * 5
      ref.current.rotation.z = state.clock.elapsedTime * 3
    }
  })

  if (!active) return null

  return (
    <group>
      {/* Attack projectile */}
      <mesh ref={ref}>
        <octahedronGeometry args={[0.8, 0]} />
        <meshBasicMaterial color="#ff0000" />
      </mesh>

      {/* Trail line */}
      <Line
        points={[new THREE.Vector3(...source), new THREE.Vector3(...target)]}
        color="#ff0000"
        lineWidth={1}
        transparent
        opacity={0.3}
        dashed
        dashSize={2}
        gapSize={1}
      />
    </group>
  )
}

// ============================================
// SUPPRESSION EFFECT
// ============================================
function SuppressionEffect({ position, type = 'quarantine', active = true }) {
  const ref = useRef()

  const colors = {
    quarantine: '#ff00ff',
    autopatch: '#00ff00',
    ebpf: '#ffff00'
  }

  useFrame((state) => {
    if (ref.current && active) {
      ref.current.scale.setScalar(1 + 0.3 * Math.sin(state.clock.elapsedTime * 3))
      ref.current.rotation.y = state.clock.elapsedTime * 2
    }
  })

  if (!active) return null

  return (
    <group position={position}>
      <mesh ref={ref}>
        <torusGeometry args={[5, 0.3, 16, 32]} />
        <meshBasicMaterial
          color={colors[type]}
          transparent
          opacity={0.8}
        />
      </mesh>

      {/* Expanding pulse rings */}
      {[1, 2, 3].map(i => (
        <ExpandingRing key={i} delay={i * 0.3} color={colors[type]} />
      ))}
    </group>
  )
}

function ExpandingRing({ delay, color }) {
  const ref = useRef()

  useFrame((state) => {
    if (ref.current) {
      const t = (state.clock.elapsedTime + delay) % 2
      ref.current.scale.setScalar(1 + t * 3)
      ref.current.material.opacity = 0.5 * (1 - t / 2)
    }
  })

  return (
    <mesh ref={ref} rotation={[Math.PI / 2, 0, 0]}>
      <ringGeometry args={[4, 4.5, 32]} />
      <meshBasicMaterial
        color={color}
        transparent
        opacity={0.5}
        side={THREE.DoubleSide}
      />
    </mesh>
  )
}

// ============================================
// GRID FLOOR
// ============================================
function GridFloor() {
  return (
    <group position={[0, -20, 0]}>
      <gridHelper args={[200, 40, '#003344', '#002233']} />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, 0]}>
        <planeGeometry args={[200, 200]} />
        <meshBasicMaterial color="#000011" transparent opacity={0.8} />
      </mesh>
    </group>
  )
}

// ============================================
// MAIN SCENE
// ============================================
function Scene({
  nodes,
  edges,
  vulnerabilities,
  attacks,
  suppressions,
  selectedNode,
  onSelectNode,
  showEnergyField,
  showMoat,
  chaosMode
}) {
  return (
    <>
      {/* Environment */}
      <ambientLight intensity={0.3} />
      <pointLight position={[50, 50, 50]} intensity={1} color="#ffffff" />
      <pointLight position={[-50, 30, -50]} intensity={0.5} color="#00ffff" />

      {/* Chaos mode lighting */}
      {chaosMode && (
        <>
          <pointLight position={[0, 30, 0]} intensity={2} color="#ff0000" />
          <pointLight position={[30, 10, 30]} intensity={1.5} color="#ff6600" />
        </>
      )}

      {/* Stars background */}
      <Stars
        radius={300}
        depth={50}
        count={5000}
        factor={4}
        saturation={0}
        fade
        speed={1}
      />

      {/* Grid floor */}
      <GridFloor />

      {/* Energy field */}
      <EnergyField visible={showEnergyField} />

      {/* Zero Trust Moat */}
      <ZeroTrustMoat active={showMoat} />

      {/* Network edges */}
      {edges.map((edge, idx) => (
        <NetworkEdge
          key={idx}
          start={edge.start}
          end={edge.end}
          active={edge.active}
          dataFlow={edge.dataFlow}
        />
      ))}

      {/* Network nodes */}
      {nodes.map(node => (
        <NetworkNode
          key={node.id}
          id={node.id}
          position={node.position}
          type={node.type}
          vulnerabilities={vulnerabilities.filter(v => v.nodeId === node.id)}
          isSelected={selectedNode === node.id}
          onSelect={onSelectNode}
          energy={node.energy || 0}
        />
      ))}

      {/* Attack probes */}
      {attacks.map((attack, idx) => (
        <AttackProbe
          key={idx}
          source={attack.source}
          target={attack.target}
          active={attack.active}
        />
      ))}

      {/* Suppression effects */}
      {suppressions.map((supp, idx) => (
        <SuppressionEffect
          key={idx}
          position={supp.position}
          type={supp.type}
          active={supp.active}
        />
      ))}

      {/* Camera controls */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={20}
        maxDistance={200}
        autoRotate={!selectedNode}
        autoRotateSpeed={0.5}
      />

      {/* Post-processing effects */}
      <EffectComposer>
        <Bloom
          luminanceThreshold={0.2}
          luminanceSmoothing={0.9}
          intensity={chaosMode ? 1.5 : 0.5}
        />
        {chaosMode && (
          <ChromaticAberration offset={[0.002, 0.002]} />
        )}
      </EffectComposer>
    </>
  )
}

// ============================================
// MAIN VULNSPHERE3D COMPONENT
// ============================================
function VulnSphere3D({
  vulns = [],
  chaosMode = false,
  showEnergyField = true,
  showMoat = true,
  onNodeSelect
}) {
  const [selectedNode, setSelectedNode] = useState(null)

  // Generate demo network topology
  const { nodes, edges } = useMemo(() => {
    const nodeList = [
      // Central mainframe
      { id: 'mainframe-01', position: [0, 0, 0], type: 'mainframe' },

      // Inner ring - critical servers
      { id: 'db-primary', position: [20, 0, 0], type: 'database' },
      { id: 'db-replica', position: [-20, 0, 0], type: 'database' },
      { id: 'firewall-01', position: [0, 0, 20], type: 'firewall' },
      { id: 'firewall-02', position: [0, 0, -20], type: 'firewall' },

      // Middle ring - application servers
      { id: 'app-server-01', position: [35, 5, 15], type: 'server' },
      { id: 'app-server-02', position: [35, 5, -15], type: 'server' },
      { id: 'app-server-03', position: [-35, 5, 15], type: 'server' },
      { id: 'app-server-04', position: [-35, 5, -15], type: 'server' },

      // Outer ring - containers and VMs
      { id: 'k8s-pod-01', position: [50, 0, 0], type: 'container' },
      { id: 'k8s-pod-02', position: [-50, 0, 0], type: 'container' },
      { id: 'k8s-pod-03', position: [0, 0, 50], type: 'container' },
      { id: 'k8s-pod-04', position: [0, 0, -50], type: 'container' },
      { id: 'vm-azure-01', position: [40, 0, 40], type: 'vm' },
      { id: 'vm-azure-02', position: [-40, 0, 40], type: 'vm' },
      { id: 'vm-aws-01', position: [40, 0, -40], type: 'vm' },
      { id: 'vm-aws-02', position: [-40, 0, -40], type: 'vm' },

      // IoT edge devices
      { id: 'iot-sensor-01', position: [60, -5, 30], type: 'iot' },
      { id: 'iot-sensor-02', position: [-60, -5, 30], type: 'iot' },
      { id: 'iot-sensor-03', position: [60, -5, -30], type: 'iot' },
      { id: 'iot-sensor-04', position: [-60, -5, -30], type: 'iot' },
    ]

    // Generate edges (connections)
    const edgeList = [
      // Mainframe to databases
      { start: [0, 0, 0], end: [20, 0, 0], active: true, dataFlow: true },
      { start: [0, 0, 0], end: [-20, 0, 0], active: true, dataFlow: true },

      // Mainframe to firewalls
      { start: [0, 0, 0], end: [0, 0, 20], active: true, dataFlow: false },
      { start: [0, 0, 0], end: [0, 0, -20], active: true, dataFlow: false },

      // Firewalls to app servers
      { start: [0, 0, 20], end: [35, 5, 15], active: true, dataFlow: true },
      { start: [0, 0, 20], end: [-35, 5, 15], active: true, dataFlow: true },
      { start: [0, 0, -20], end: [35, 5, -15], active: true, dataFlow: true },
      { start: [0, 0, -20], end: [-35, 5, -15], active: true, dataFlow: true },

      // App servers to containers
      { start: [35, 5, 15], end: [50, 0, 0], active: true, dataFlow: true },
      { start: [35, 5, -15], end: [0, 0, -50], active: true, dataFlow: true },
      { start: [-35, 5, 15], end: [-50, 0, 0], active: true, dataFlow: true },
      { start: [-35, 5, -15], end: [0, 0, 50], active: true, dataFlow: true },

      // App servers to VMs
      { start: [35, 5, 15], end: [40, 0, 40], active: true, dataFlow: false },
      { start: [35, 5, -15], end: [40, 0, -40], active: true, dataFlow: false },
      { start: [-35, 5, 15], end: [-40, 0, 40], active: true, dataFlow: false },
      { start: [-35, 5, -15], end: [-40, 0, -40], active: true, dataFlow: false },

      // VMs to IoT
      { start: [40, 0, 40], end: [60, -5, 30], active: false, dataFlow: false },
      { start: [-40, 0, 40], end: [-60, -5, 30], active: false, dataFlow: false },
      { start: [40, 0, -40], end: [60, -5, -30], active: false, dataFlow: false },
      { start: [-40, 0, -40], end: [-60, -5, -30], active: false, dataFlow: false },
    ]

    return { nodes: nodeList, edges: edgeList }
  }, [])

  // Demo attacks
  const attacks = useMemo(() => {
    if (!chaosMode) return []
    return [
      { source: [100, 20, 50], target: [50, 0, 0], active: true },
      { source: [-100, 30, -30], target: [-50, 0, 0], active: true },
    ]
  }, [chaosMode])

  // Suppressions based on selected node
  const suppressions = useMemo(() => {
    if (!selectedNode) return []
    const node = nodes.find(n => n.id === selectedNode)
    if (!node) return []
    return [{ position: node.position, type: 'quarantine', active: true }]
  }, [selectedNode, nodes])

  const handleNodeSelect = useCallback((nodeId) => {
    setSelectedNode(prev => prev === nodeId ? null : nodeId)
    onNodeSelect && onNodeSelect(nodeId)
  }, [onNodeSelect])

  return (
    <div className="vulnsphere-3d" style={{ width: '100%', height: '100%' }}>
      <Canvas
        camera={{ position: [80, 60, 80], fov: 60 }}
        gl={{ antialias: true, alpha: false }}
        style={{ background: '#000011' }}
      >
        <Suspense fallback={null}>
          <Scene
            nodes={nodes}
            edges={edges}
            vulnerabilities={vulns}
            attacks={attacks}
            suppressions={suppressions}
            selectedNode={selectedNode}
            onSelectNode={handleNodeSelect}
            showEnergyField={showEnergyField}
            showMoat={showMoat}
            chaosMode={chaosMode}
          />
        </Suspense>
      </Canvas>

      {/* HUD Overlay */}
      <div className="hud-overlay">
        <div className="hud-stats">
          <div className="hud-stat">
            <span className="hud-label">NODES</span>
            <span className="hud-value">{nodes.length}</span>
          </div>
          <div className="hud-stat">
            <span className="hud-label">VULNS</span>
            <span className="hud-value critical">{vulns.length}</span>
          </div>
          <div className="hud-stat">
            <span className="hud-label">STATUS</span>
            <span className={`hud-value ${chaosMode ? 'danger' : 'safe'}`}>
              {chaosMode ? 'ALERT' : 'SECURE'}
            </span>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="controls-hint">
        <span>Drag to rotate</span>
        <span>Scroll to zoom</span>
        <span>Click node to select</span>
      </div>
    </div>
  )
}

export default VulnSphere3D
