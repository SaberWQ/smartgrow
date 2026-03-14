/**
 * SmartGrow 3D Plant Pet Visualization
 * =====================================
 * 
 * Interactive 3D plant with emotional states.
 * The plant reacts to sensor data and user interactions.
 */

import { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { 
  OrbitControls, 
  Environment,
  Float,
  MeshWobbleMaterial,
  Html
} from '@react-three/drei';
import * as THREE from 'three';

import type { PlantMood } from '../types';

// Plant growth stages
type GrowthStage = 'seed' | 'sprout' | 'seedling' | 'vegetative' | 'flowering' | 'mature';

interface Plant3DProps {
  growthStage: GrowthStage;
  moisture: number;
  temperature: number;
  health: number;
  isWatering: boolean;
  lightOn: boolean;
  mood?: PlantMood;
  onClick?: () => void;
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

// Mood colors for ambient light
const MOOD_AMBIENT: Record<PlantMood, string> = {
  happy: '#90EE90',
  thirsty: '#FFA500',
  hot: '#FF6B6B',
  cold: '#87CEEB',
  sick: '#DDA0DD',
  sleepy: '#9370DB',
  excited: '#FFD700',
  neutral: '#98FB98'
};

// Face expressions component
function PlantFace({ 
  mood, 
  position 
}: { 
  mood: PlantMood;
  position: [number, number, number];
}) {
  const faceRef = useRef<THREE.Group>(null);
  const [blink, setBlink] = useState(false);
  
  // Blinking animation
  useFrame((state) => {
    if (faceRef.current) {
      // Subtle bobbing
      faceRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.02;
      
      // Occasional blink
      if (Math.random() < 0.005) {
        setBlink(true);
        setTimeout(() => setBlink(false), 150);
      }
    }
  });
  
  const eyeHeight = blink ? 0.01 : 0.03;
  const mouthCurve = mood === 'happy' || mood === 'excited' ? 0.03 : 
                     mood === 'thirsty' || mood === 'sick' ? -0.02 : 0;
  
  // Eye style based on mood
  const getEyeStyle = () => {
    switch (mood) {
      case 'sleepy':
        return { scaleY: 0.3 };
      case 'excited':
        return { scaleY: 1.2 };
      case 'thirsty':
        return { scaleY: 0.7 };
      default:
        return { scaleY: 1 };
    }
  };
  
  const eyeStyle = getEyeStyle();
  
  return (
    <group ref={faceRef} position={position}>
      {/* Left eye */}
      <mesh position={[-0.08, 0, 0.15]} scale={[1, eyeStyle.scaleY, 1]}>
        <sphereGeometry args={[0.02, 8, 8]} />
        <meshBasicMaterial color="#1a1a2e" />
      </mesh>
      
      {/* Right eye */}
      <mesh position={[0.08, 0, 0.15]} scale={[1, eyeStyle.scaleY, 1]}>
        <sphereGeometry args={[0.02, 8, 8]} />
        <meshBasicMaterial color="#1a1a2e" />
      </mesh>
      
      {/* Mouth */}
      <mesh position={[0, -0.06, 0.14]} rotation={[0, 0, 0]}>
        <torusGeometry args={[0.04, 0.01, 8, 16, Math.PI]} />
        <meshBasicMaterial color="#1a1a2e" />
      </mesh>
      
      {/* Blush for happy/excited */}
      {(mood === 'happy' || mood === 'excited') && (
        <>
          <mesh position={[-0.12, -0.02, 0.12]}>
            <circleGeometry args={[0.025, 16]} />
            <meshBasicMaterial color="#FFB6C1" transparent opacity={0.5} />
          </mesh>
          <mesh position={[0.12, -0.02, 0.12]}>
            <circleGeometry args={[0.025, 16]} />
            <meshBasicMaterial color="#FFB6C1" transparent opacity={0.5} />
          </mesh>
        </>
      )}
      
      {/* Sweat drop for hot/thirsty */}
      {(mood === 'hot' || mood === 'thirsty') && (
        <mesh position={[0.15, 0.05, 0.1]}>
          <sphereGeometry args={[0.015, 8, 8]} />
          <meshBasicMaterial color="#87CEEB" transparent opacity={0.8} />
        </mesh>
      )}
      
      {/* ZZZ for sleepy */}
      {mood === 'sleepy' && (
        <Html position={[0.2, 0.1, 0]} style={{ pointerEvents: 'none' }}>
          <div className="text-indigo-400 font-bold text-lg animate-pulse">zzZ</div>
        </Html>
      )}
    </group>
  );
}

// Leaf component with droop based on moisture
function Leaf({ 
  position, 
  rotation, 
  scale, 
  health, 
  moisture,
  index,
  mood
}: { 
  position: [number, number, number];
  rotation: [number, number, number];
  scale: number;
  health: number;
  moisture: number;
  index: number;
  mood: PlantMood;
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
      // Gentle swaying animation - more active when excited
      const swayIntensity = mood === 'excited' ? 0.2 : mood === 'sleepy' ? 0.02 : 0.1;
      leafRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.5 + index) * swayIntensity;
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
        factor={mood === 'excited' ? 0.4 : 0.2}
        speed={mood === 'sleepy' ? 0.5 : 1}
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
  scale,
  mood
}: { 
  position: [number, number, number];
  scale: number;
  mood: PlantMood;
}) {
  const flowerRef = useRef<THREE.Group>(null);
  
  useFrame((state) => {
    if (flowerRef.current) {
      const speed = mood === 'excited' ? 0.6 : mood === 'sleepy' ? 0.1 : 0.3;
      flowerRef.current.rotation.y = state.clock.elapsedTime * speed;
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
    if (dropletsRef.current && active && dropletsRef.current.geometry) {
      const posAttr = dropletsRef.current.geometry.attributes.position;
      if (posAttr) {
        const positions = posAttr.array as Float32Array;
        
        for (let i = 0; i < positions.length; i += 3) {
          positions[i + 1] -= 0.05; // Fall down
          
          if (positions[i + 1] < -0.2) {
            positions[i + 1] = 1.5; // Reset to top
          }
        }
        
        posAttr.needsUpdate = true;
      }
    }
  });
  
  if (!active) return null;
  
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(particles, 3));
    return geo;
  }, [particles]);
  
  return (
    <points ref={dropletsRef} geometry={geometry}>
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
function SeedPlant({ mood }: { mood: PlantMood }) {
  return (
    <group>
      <mesh position={[0, 0.05, 0]}>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshStandardMaterial 
          color="#8b4513"
          roughness={0.8}
        />
      </mesh>
      <PlantFace mood={mood} position={[0, 0.08, 0]} />
    </group>
  );
}

// Sprout stage
function SproutPlant({ health, mood }: { health: number; mood: PlantMood }) {
  return (
    <group>
      <Stem height={0.15} health={health} />
      <PlantFace mood={mood} position={[0, 0.18, 0]} />
      <Leaf 
        position={[0.05, 0.15, 0]} 
        rotation={[0.3, 0, 0.5]} 
        scale={0.5}
        health={health}
        moisture={50}
        index={0}
        mood={mood}
      />
      <Leaf 
        position={[-0.05, 0.12, 0]} 
        rotation={[0.3, Math.PI, -0.5]} 
        scale={0.4}
        health={health}
        moisture={50}
        index={1}
        mood={mood}
      />
    </group>
  );
}

// Full plant (seedling to mature)
function FullPlant({ 
  stage, 
  health, 
  moisture,
  mood
}: { 
  stage: GrowthStage;
  health: number;
  moisture: number;
  mood: PlantMood;
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
        mood={mood}
      />
    );
  }
  
  return (
    <group scale={scale}>
      <Stem height={height} health={health} />
      <PlantFace mood={mood} position={[0, height * 0.7, 0]} />
      {leaves}
      {showFlowers && (
        <>
          <Flower position={[0, height + 0.1, 0]} scale={stage === 'mature' ? 1.2 : 0.8} mood={mood} />
          {stage === 'mature' && (
            <>
              <Flower position={[0.15, height - 0.1, 0.1]} scale={0.6} mood={mood} />
              <Flower position={[-0.12, height - 0.15, -0.1]} scale={0.5} mood={mood} />
            </>
          )}
        </>
      )}
    </group>
  );
}

// Click indicator
function ClickIndicator() {
  return (
    <Html center position={[0, -0.6, 0]} style={{ pointerEvents: 'none' }}>
      <div className="text-xs text-zinc-500 animate-pulse">Click to chat</div>
    </Html>
  );
}

// Main plant scene
function PlantScene({ 
  growthStage, 
  moisture, 
  temperature, 
  health,
  isWatering,
  lightOn,
  mood = 'neutral',
  onClick
}: Plant3DProps) {
  const groupRef = useRef<THREE.Group>(null);
  
  // Bounce on click
  const handleClick = () => {
    if (onClick) onClick();
  };
  
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} color={MOOD_AMBIENT[mood]} />
      <directionalLight position={[5, 5, 5]} intensity={0.8} castShadow />
      <pointLight position={[-3, 2, -3]} intensity={0.3} color="#90ee90" />
      
      {/* UV Light effect */}
      <UVLight active={lightOn} />
      
      {/* Environment */}
      <Environment preset="park" />
      
      {/* Plant based on growth stage */}
      <Float speed={1} rotationIntensity={0.1} floatIntensity={0.1}>
        <group ref={groupRef} position={[0, 0.1, 0]} onClick={handleClick}>
          {growthStage === 'seed' && <SeedPlant mood={mood} />}
          {growthStage === 'sprout' && <SproutPlant health={health} mood={mood} />}
          {['seedling', 'vegetative', 'flowering', 'mature'].includes(growthStage) && (
            <FullPlant stage={growthStage} health={health} moisture={moisture} mood={mood} />
          )}
        </group>
      </Float>
      
      {/* Pot */}
      <Pot />
      
      {/* Water droplets */}
      <WaterDroplets active={isWatering} />
      
      {/* Click indicator */}
      {onClick && <ClickIndicator />}
      
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
  // Derive mood from sensor data if not provided
  const derivedMood = props.mood || (
    props.moisture < 30 ? 'thirsty' :
    props.temperature > 35 ? 'hot' :
    props.temperature < 10 ? 'cold' :
    props.health < 40 ? 'sick' :
    props.health > 80 ? 'happy' : 'neutral'
  );
  
  return (
    <div className="w-full h-full min-h-[300px] rounded-xl overflow-hidden bg-gradient-to-b from-zinc-900 to-zinc-950 cursor-pointer">
      <Canvas
        shadows
        camera={{ position: [2, 1.5, 2], fov: 50 }}
        gl={{ antialias: true }}
      >
        <PlantScene {...props} mood={derivedMood} />
      </Canvas>
      
      {/* Status overlay */}
      <div className="absolute bottom-4 left-4 right-4 flex justify-between text-xs text-zinc-400">
        <span className="capitalize">{derivedMood}</span>
        <span>{props.growthStage}</span>
        <span>HP: {props.health}%</span>
      </div>
    </div>
  );
}
