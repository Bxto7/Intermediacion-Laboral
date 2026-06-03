import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, Sphere } from '@react-three/drei'
import { useRef } from 'react'
import * as THREE from 'three'

interface KPINode {
  label: string
  value: number
  color: string
  position: [number, number, number]
}

const NODE_DATA: KPINode[] = [
  { label: 'Trabajadores', value: 2400, color: '#b8442a', position: [0, 0, 0] },
  { label: 'Ofertas',      value: 180,  color: '#0f6e6e', position: [3, 1, -1] },
  { label: 'Contratos',    value: 95,   color: '#7a8c5c', position: [-2.5, 1.5, 1] },
  { label: 'Matching',     value: 87,   color: '#c9961f', position: [1.5, -2, 1.5] },
  { label: 'Empresas',     value: 340,  color: '#6c4fa3', position: [-1.5, -1.5, -2] },
]

const FloatingNode = ({ node }: { node: KPINode }) => {
  const meshRef = useRef<THREE.Mesh>(null)
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.position.y = node.position[1] + Math.sin(state.clock.elapsedTime + node.position[0]) * 0.15
    }
  })
  const scale = 0.3 + (node.value / 2400) * 0.7

  return (
    <group position={node.position}>
      <Sphere ref={meshRef} args={[scale, 32, 32]}>
        <meshStandardMaterial color={node.color} roughness={0.2} metalness={0.4} />
      </Sphere>
      <Text
        position={[0, scale + 0.3, 0]}
        fontSize={0.22}
        color="white"
        anchorX="center"
        anchorY="bottom"
      >
        {node.label}
      </Text>
      <Text
        position={[0, scale + 0.05, 0]}
        fontSize={0.18}
        color={node.color}
        anchorX="center"
        anchorY="top"
      >
        {node.value.toLocaleString()}
      </Text>
    </group>
  )
}

export const KPIGlobe: React.FC = () => (
  <div style={{ width: '100%', height: 340, borderRadius: 16, overflow: 'hidden', background: 'linear-gradient(160deg, #150d06 0%, #241910 100%)' }}>
    <Canvas camera={{ position: [0, 0, 8], fov: 50 }}>
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={1.2} color="#b8442a" />
      <pointLight position={[-10, -5, -5]} intensity={0.6} color="#0f6e6e" />
      {NODE_DATA.map(n => <FloatingNode key={n.label} node={n} />)}
      <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.8} />
    </Canvas>
  </div>
)
