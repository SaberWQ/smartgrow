/**
 * SmartGrow 3D Plant Visualization
 * ================================
 * 
 * Interactive 3D plant that grows based on real sensor data.
 * Uses React Three Fiber for rendering.
 */

import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { 
  OrbitControls, 
  Environment,
  Float,
  MeshWobbleMaterial,
  Text3D,
  Center
} from '@react-three/drei';
import * as THREE from 'three';

// Plant growth stages
type GrowthStage = 'seed' | 'sprout' | 'seedling' | 'vegetative' | 'flowering' | 'mature';

interface Plant3DProps {
  growthStage: GrowthStage;
  moisture: number;
  temperature: number;
  health: number;
  isWatering: boolean;
  lightOn: boolean;
}

// Growth stage to scale mapping
const STAGE_SCALES: Record<GrowthStage, number> = {
  seed: 0.2,
  sprout: 0.4,
  seedling: 0.6,
  vegetative: 0.8,
  flowering: 0.95,
  mature: 1.0
};

// Leaf component
function Leaf({ 
  position, 
  rotation, 
  scale, 
  health, 
  moisture,
  index 
}: { 
  position: [number, number, number];
  rotation: [number, number, number];
  scale: number;
  health: number;
  moisture: number;
  index: number;
}) {
  const leafRef = useRef<THREE.Mesh>(null);
  
  // Calculate leaf color based on health and moisture
  const leafColor = useMemo(() => {
    const healthFactor = health / 100;
    const moistureFactor = Math.min(moisture / 50, 1);
    
    // Green when healthy, yellow/brown when stressed
    const r = 0.1 + (1 - healthFactor) * 0.5;
    const g = 0.5 + healthFactor * 0.3 + moistureFactor * 0.2;
    const b = 0.1;
    
    return new THREE.Color(r, g, b);
  }, [health, moisture]);
  
  // Drooping effect when low moisture
  const droopAngle = useMemo(() => {
    if (moisture < 30) return -0.5;
    if (moisture < 50) return -0.2;
    return 0;
  }, [moisture]);
  
  useFrame((state) => {
    if (leafRef.current) {
      // Gentle swaying animation
      leafRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.5 + index) * 0.1;
      leafRef.current.rotation.x = rotation[0] + droopAngle + Math.sin(state.clock.elapsedTime * 0.3 + index) * 0.05;
    }
  });
  
  return (
    <mesh 
      ref={leafRef}
      position={position} 
      rotation={rotation}
      scale={scale}
    >
      <sphereGeometry args={[0.15, 8, 4]} />
      <MeshWobbleMaterial 
        color={leafColor}
        factor={0.2}
        speed={1}
        roughness={0.8}
        metalness={0.1}
      />
    </mesh>
  );
}

// Stem component
function Stem({ 
  height, 
  health 
}: { 
  height: number; 
  health: number;
}) {
  const stemRef = useRef<THREE.Mesh>(null);
  
  const stemColor = useMemo(() => {
    const healthFactor = health / 100;
    return new THREE.Color(0.2, 0.4 + healthFactor * 0.2, 0.1);
  }, [health]);
  
  useFrame((state) => {
    if (stemRef.current) {
      // Subtle sway
      stemRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.02;
      stemRef.current.rotation.z = Math.cos(state.clock.elapsedTime * 0.15) * 0.02;
    }
  });
  
  return (
    <mesh ref={stemRef} position={[0, height / 2, 0]}>
      <cylinderGeometry args={[0.03, 0.05, height, 8]} />
      <meshStandardMaterial 
        color={stemColor}
        roughness={0.9}
        metalness={0}
      />
    </mesh>
  );
}

// Flower component (for flowering/mature stages)
function Flower({ 
  position, 
  scale 
}: { 
  position: [number, number, number];
  scale: number;
}) {
  const flowerRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (flowerRef.current) {
      flowerRef.current.rotation.y = state.clock.elapsedTime * 0.3;
    }
  });
  
  const petalCount = 5;
  const petals = [];
  
  for (let i = 0; i < petalCount; i++) {
    const angle = (i / petalCount) * Math.PI * 2;
    petals.push(
      <mesh 
        key={i}
        position={[Math.cos(angle) * 0.1, 0, Math.sin(angle) * 0.1]}
        rotation={[0.5, angle, 0]}
      >
        <sphereGeometry args={[0.08, 8, 4]} />
        <meshStandardMaterial 
          color="#ff69b4"
          roughness={0.5}
          metalness={0.2}
        />
      </mesh>
    );
  }
  
  return (
    <group ref={flowerRef} position={position} scale={scale}>
      {/* Center */}
      <mesh>
        <sphereGeometry args={[0.05, 16, 16]} />
        <meshStandardMaterial color="#ffd700" />
      </mesh>
      {/* Petals */}
      {petals}
    </group>
  );
}

// Pot component
function Pot() {
  return (
    <group position={[0, -0.3, 0]}>
      {/* Pot body */}
      <mesh>
        <cylinderGeometry args={[0.35, 0.25, 0.4, 16]} />
        <meshStandardMaterial 
          color="#8b4513"
          roughness={0.9}
          metalness={0}
        />
      </mesh>
      {/* Pot rim */}
      <mesh position={[0, 0.2, 0]}>
        <torusGeometry args={[0.35, 0.03, 8, 24]} />
        <meshStandardMaterial color="#6b3513" />
      </mesh>
      {/* Soil */}
      <mesh position={[0, 0.1, 0]}>
        <cylinderGeometry args={[0.32, 0.32, 0.1, 16]} />
        <meshStandardMaterial 
          color="#3d2817"
          roughness={1}
          metalness={0}
        />
      </mesh>
    </group>
  );
}

// Water droplets effect
function WaterDroplets({ active }: { active: boolean }) {
  const dropletsRef = useRef<THREE.Points>(null);
  
  const particles = useMemo(() => {
    const count = 50;
    const positions = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 0.5;
      positions[i * 3 + 1] = Math.random() * 1.5;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 0.5;
    }
    
    return positions;
  }, []);
  
  useFrame(() => {
    if (dropletsRef.current && active) {
      const positions = dropletsRef.current.geometry.attributes.position.array as Float32Array;
      
      for (let i = 0; i < positions.length; i += 3) {
        positions[i + 1] -= 0.05; // Fall down
        
        if (positions[i + 1] < -0.2) {
          positions[i + 1] = 1.5; // Reset to top
        }
      }
      
      dropletsRef.current.geometry.attributes.position.needsUpdate = true;
    }
  });
  
  if (!active) return null;
  
  return (
    <points ref={dropletsRef}>
      <bufferGeometry>
        <bufferAttribute 
          attach="attributes-position"
          count={particles.length / 3}
          array={particles}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial 
        size={0.02}
        color="#00bfff"
        transparent
        opacity={0.8}
      />
    </points>
  );
}

// UV Light effect
function UVLight({ active }: { active: boolean }) {
  const lightRef = useRef<THREE.SpotLight>(null);
  
  useFrame((state) => {
    if (lightRef.current && active) {
      lightRef.current.intensity = 2 + Math.sin(state.clock.elapsedTime * 2) * 0.3;
    }
  });
  
  if (!active) return null;
  
  return (
    <>
      <spotLight
        ref={lightRef}
        position={[0, 3, 0]}
        angle={0.6}
        penumbra={0.5}
        intensity={2}
        color="#9932cc"
        castShadow
      />
      {/* Light cone visualization */}
      <mesh position={[0, 2.5, 0]} rotation={[Math.PI, 0, 0]}>
        <coneGeometry args={[0.3, 0.5, 16, 1, true]} />
        <meshBasicMaterial 
          color="#9932cc"
          transparent
          opacity={0.2}
          side={THREE.DoubleSide}
        />
      </mesh>
    </>
  );
}

// Seed stage
function SeedPlant() {
  return (
    <mesh position={[0, 0.05, 0]}>
      <sphereGeometry args={[0.08, 16, 16]} />
      <meshStandardMaterial 
        color="#8b4513"
        roughness={0.8}
      />
    </mesh>
  );
}

// Sprout stage
function SproutPlant({ health }: { health: number }) {
  return (
    <group>
      <Stem height={0.15} health={health} />
      <Leaf 
        position={[0.05, 0.15, 0]} 
        rotation={[0.3, 0, 0.5]} 
        scale={0.5}
        health={health}
        moisture={50}
        index={0}
      />
      <Leaf 
        position={[-0.05, 0.12, 0]} 
        rotation={[0.3, Math.PI, -0.5]} 
        scale={0.4}
        health={health}
        moisture={50}
        index={1}
      />
    </group>
  );
}

// Full plant (seedling to mature)
function FullPlant({ 
  stage, 
  health, 
  moisture 
}: { 
  stage: GrowthStage;
  health: number;
  moisture: number;
}) {
  const scale = STAGE_SCALES[stage];
  const showFlowers = stage === 'flowering' || stage === 'mature';
  
  const leafCount = useMemo(() => {
    switch(stage) {
      case 'seedling': return 4;
      case 'vegetative': return 8;
      case 'flowering': return 10;
      case 'mature': return 12;
      default: return 4;
    }
  }, [stage]);
  
  const height = scale * 1.2;
  
  const leaves = [];
  for (let i = 0; i < leafCount; i++) {
    const heightRatio = (i + 1) / leafCount;
    const angle = (i / leafCount) * Math.PI * 2 + Math.random() * 0.5;
    const distance = 0.1 + heightRatio * 0.15;
    
    leaves.push(
      <Leaf
        key={i}
        position={[
          Math.cos(angle) * distance,
          heightRatio * height * 0.8,
          Math.sin(angle) * distance
        ]}
        rotation={[
          0.3 + (1 - heightRatio) * 0.3,
          angle,
          0.2
        ]}
        scale={0.6 + heightRatio * 0.4}
        health={health}
        moisture={moisture}
        index={i}
      />
    );
  }
  
  return (
    <group scale={scale}>
      <Stem height={height} health={health} />
      {leaves}
      {showFlowers && (
        <>
          <Flower position={[0, height + 0.1, 0]} scale={stage === 'mature' ? 1.2 : 0.8} />
          {stage === 'mature' && (
            <>
              <Flower position={[0.15, height - 0.1, 0.1]} scale={0.6} />
              <Flower position={[-0.12, height - 0.15, -0.1]} scale={0.5} />
            </>
          )}
        </>
      )}
    </group>
  );
}

// Main plant scene
function PlantScene({ 
  growthStage, 
  moisture, 
  temperature, 
  health,
  isWatering,
  lightOn
}: Plant3DProps) {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 5, 5]} intensity={0.8} castShadow />
      <pointLight position={[-3, 2, -3]} intensity={0.3} color="#90ee90" />
      
      {/* UV Light effect */}
      <UVLight active={lightOn} />
      
      {/* Environment */}
      <Environment preset="park" />
      
      {/* Plant based on growth stage */}
      <Float speed={1} rotationIntensity={0.1} floatIntensity={0.1}>
        <group position={[0, 0.1, 0]}>
          {growthStage === 'seed' && <SeedPlant />}
          {growthStage === 'sprout' && <SproutPlant health={health} />}
          {['seedling', 'vegetative', 'flowering', 'mature'].includes(growthStage) && (
            <FullPlant stage={growthStage} health={health} moisture={moisture} />
          )}
        </group>
      </Float>
      
      {/* Pot */}
      <Pot />
      
      {/* Water droplets */}
      <WaterDroplets active={isWatering} />
      
      {/* Controls */}
      <OrbitControls 
        enableZoom={true}
        enablePan={false}
        minDistance={2}
        maxDistance={5}
        minPolarAngle={Math.PI / 6}
        maxPolarAngle={Math.PI / 2}
      />
    </>
  );
}

// Main component export
export default function Plant3D(props: Plant3DProps) {
  return (
    <div className="w-full h-full min-h-[300px] rounded-xl overflow-hidden bg-gradient-to-b from-zinc-900 to-zinc-950">
      <Canvas
        shadows
        camera={{ position: [2, 1.5, 2], fov: 50 }}
        gl={{ antialias: true }}
      >
        <PlantScene {...props} />
      </Canvas>
      
      {/* Status overlay */}
      <div className="absolute bottom-4 left-4 right-4 flex justify-between text-xs text-zinc-400">
        <span>Stage: {props.growthStage}</span>
        <span>Health: {props.health}%</span>
      </div>
    </div>
  );
}
