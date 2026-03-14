import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Leaf, 
  Droplets, 
  Thermometer, 
  Wind, 
  Gauge,
  Sun,
  Menu,
  X,
  RefreshCw,
  Wifi,
  WifiOff,
  Server,
  Gamepad2,
  Bot
} from 'lucide-react';

// Components
import SensorCard from './components/SensorCard';
import ControlPanel from './components/ControlPanel';
import PlantStatus from './components/PlantStatus';
import AIAssistant from './components/AIAssistant';
import GamePanel from './components/GamePanel';
import SystemLogs from './components/SystemLogs';
import SensorChart from './components/SensorChart';
import Plant3D from './components/Plant3D';
import PlantPetChat from './components/PlantPetChat';

// Services & Data
import {
  generateSensorData,
  generateSensorHistory,
  generateSystemLogs,
  getDefaultRecommendations,
  ALL_ACHIEVEMENTS
} from './services/mockData';

import { getPlantMood } from './services/plantPetAI';

// Raspberry Pi API
import * as PiAPI from './services/raspberryPiApi';

// Types
import type { 
  SensorData, 
  GreenhouseControls, 
  PlantProfile, 
  UserProfile,
  AIRecommendation,
  DailyTask,
  Achievement,
  SystemLog,
  PlantMood,
  PlantQuest
} from './types';

// Default states
const defaultControls: GreenhouseControls = {
  pumpActive: false,
  uvLightActive: false,
  autoWateringEnabled: true,
  autoLightingEnabled: true,
  wateringThreshold: 35,
  lightingSchedule: { startHour: 7, endHour: 22 }
};

const defaultPlant: PlantProfile = {
  id: 'plant-1',
  uid: 'demo-user',
  name: 'Flora',
  species: 'Basil (Ocimum basilicum)',
  plantedAt: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(), // 14 days ago
  health: 85,
  growthStage: 'seedling',
  growthProgress: 35,
  totalWaterings: 12,
  mood: 'happy',
  personality: {
    friendliness: 80,
    curiosity: 70,
    dramaticLevel: 60
  }
};

const defaultProfile: UserProfile = {
  uid: 'demo-user',
  displayName: 'Plant Guardian',
  email: 'demo@smartgrow.app',
  level: 3,
  xp: 450,
  gold: 125,
  totalWaterings: 24,
  totalUVSessions: 18,
  streak: 7
};

const defaultTasks: DailyTask[] = [
  {
    id: 'task-1',
    uid: 'demo-user',
    title: 'Morning Hydration Ritual',
    description: 'Check soil moisture and water if needed',
    type: 'water',
    rewardXp: 25,
    rewardGold: 10,
    completed: false,
    createdAt: new Date().toISOString()
  },
  {
    id: 'task-2',
    uid: 'demo-user',
    title: 'Sensor Patrol',
    description: 'Review all sensor readings for anomalies',
    type: 'check_sensors',
    rewardXp: 15,
    rewardGold: 5,
    completed: true,
    createdAt: new Date().toISOString(),
    completedAt: new Date().toISOString()
  },
  {
    id: 'task-3',
    uid: 'demo-user',
    title: 'Light Guardian Duty',
    description: 'Ensure UV light is optimized for growth',
    type: 'adjust_light',
    rewardXp: 30,
    rewardGold: 15,
    completed: false,
    createdAt: new Date().toISOString()
  },
  {
    id: 'task-4',
    uid: 'demo-user',
    title: 'Talk to Flora',
    description: 'Have a chat with your plant friend',
    type: 'ai_consultation',
    rewardXp: 20,
    rewardGold: 10,
    completed: false,
    createdAt: new Date().toISOString()
  }
];

export default function App() {
  // State
  const [sensors, setSensors] = useState<SensorData>(generateSensorData());
  const [sensorHistory, setSensorHistory] = useState<SensorData[]>(generateSensorHistory(24));
  const [controls, setControls] = useState<GreenhouseControls>(defaultControls);
  const [plant, setPlant] = useState<PlantProfile>(defaultPlant);
  const [profile, setProfile] = useState<UserProfile>(defaultProfile);
  const [recommendations, setRecommendations] = useState<AIRecommendation[]>([]);
  const [dailyTasks, setDailyTasks] = useState<DailyTask[]>(defaultTasks);
  const [achievements] = useState<Achievement[]>(
    ALL_ACHIEVEMENTS.map(a => ({
      ...a,
      unlockedAt: ['first_watering', 'streak_7'].includes(a.id) ? new Date().toISOString() : undefined
    }))
  );
  const [logs, setLogs] = useState<SystemLog[]>(generateSystemLogs(10));
  const [isConnected, setIsConnected] = useState(true);
  const [isWatering, setIsWatering] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [plantMood, setPlantMood] = useState<PlantMood>('happy');
  
  // Raspberry Pi connection mode
  const [usePiConnection, setUsePiConnection] = useState(false);
  const [piConnected, setPiConnected] = useState(false);
  const wsCleanup = useRef<(() => void) | null>(null);

  // Update plant mood based on sensors
  useEffect(() => {
    const mood = getPlantMood(sensors, plant.health);
    setPlantMood(mood);
    setPlant(prev => ({ ...prev, mood }));
  }, [sensors, plant.health]);

  // Simulate real-time sensor updates
  useEffect(() => {
    const interval = setInterval(() => {
      const newSensorData = generateSensorData();
      setSensors(newSensorData);
      setSensorHistory(prev => [...prev.slice(-23), newSensorData]);
      setLastUpdate(new Date());
      
      // Update recommendations based on new data
      setRecommendations(getDefaultRecommendations(newSensorData));
      
      // Auto-watering logic
      if (controls.autoWateringEnabled && newSensorData.soilMoisture < controls.wateringThreshold && !controls.pumpActive) {
        triggerWatering();
      }
      
      // Auto-lighting logic
      const hour = new Date().getHours();
      const shouldLightBeOn = hour >= controls.lightingSchedule.startHour && hour < controls.lightingSchedule.endHour;
      if (controls.autoLightingEnabled && shouldLightBeOn !== controls.uvLightActive) {
        setControls(prev => ({ ...prev, uvLightActive: shouldLightBeOn }));
        addLog(shouldLightBeOn ? 'UV light activated (schedule)' : 'UV light deactivated (schedule)', 'info', 'light');
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [controls]);

  // Initial recommendations
  useEffect(() => {
    setRecommendations(getDefaultRecommendations(sensors));
  }, []);

  const addLog = useCallback((message: string, type: SystemLog['type'], source: SystemLog['source']) => {
    const newLog: SystemLog = {
      id: `log-${Date.now()}`,
      type,
      message,
      timestamp: new Date().toISOString(),
      source
    };
    setLogs(prev => [newLog, ...prev.slice(0, 19)]);
  }, []);

  const triggerWatering = useCallback(() => {
    if (isWatering) return;
    
    setIsWatering(true);
    setControls(prev => ({ ...prev, pumpActive: true }));
    addLog('Watering cycle started', 'info', 'pump');
    
    // Simulate watering duration
    setTimeout(() => {
      setControls(prev => ({ ...prev, pumpActive: false }));
      setIsWatering(false);
      setSensors(prev => ({ ...prev, soilMoisture: Math.min(prev.soilMoisture + 35, 95) }));
      setPlant(prev => ({ ...prev, totalWaterings: prev.totalWaterings + 1 }));
      setProfile(prev => ({ ...prev, totalWaterings: prev.totalWaterings + 1 }));
      addLog('Watering cycle completed', 'success', 'pump');
    }, 3000);
  }, [isWatering, addLog]);

  const handleTogglePump = () => {
    if (controls.pumpActive) {
      setControls(prev => ({ ...prev, pumpActive: false }));
      setIsWatering(false);
      addLog('Pump manually stopped', 'info', 'pump');
    } else {
      triggerWatering();
    }
  };

  const handleToggleUV = () => {
    setControls(prev => ({ ...prev, uvLightActive: !prev.uvLightActive }));
    addLog(controls.uvLightActive ? 'UV light turned off' : 'UV light turned on', 'info', 'light');
  };

  const handleToggleAutoWatering = () => {
    setControls(prev => ({ ...prev, autoWateringEnabled: !prev.autoWateringEnabled }));
    addLog(controls.autoWateringEnabled ? 'Auto-watering disabled' : 'Auto-watering enabled', 'info', 'system');
  };

  const handleToggleAutoLighting = () => {
    setControls(prev => ({ ...prev, autoLightingEnabled: !prev.autoLightingEnabled }));
    addLog(controls.autoLightingEnabled ? 'Auto-lighting disabled' : 'Auto-lighting enabled', 'info', 'system');
  };

  const handleDismissRecommendation = (id: string) => {
    setRecommendations(prev => prev.filter(r => r.id !== id));
  };

  const handleAIAction = (action: string) => {
    if (action === 'water') {
      triggerWatering();
    } else if (action === 'light_on') {
      setControls(prev => ({ ...prev, uvLightActive: true }));
      addLog('UV light activated by AI', 'success', 'ai');
    } else if (action === 'light_off') {
      setControls(prev => ({ ...prev, uvLightActive: false }));
      addLog('UV light deactivated by AI', 'info', 'ai');
    }
    // Remove the recommendation that triggered this action
    setRecommendations(prev => prev.filter(r => r.action !== action));
  };

  // Handle voice/chat commands
  const handlePlantAction = (action: string) => {
    switch (action) {
      case 'water':
        triggerWatering();
        break;
      case 'light_on':
        setControls(prev => ({ ...prev, uvLightActive: true }));
        addLog('UV light activated by voice', 'success', 'voice');
        break;
      case 'light_off':
        setControls(prev => ({ ...prev, uvLightActive: false }));
        addLog('UV light deactivated by voice', 'info', 'voice');
        break;
      case 'health_check':
        addLog(`Plant health: ${plant.health}%, Mood: ${plantMood}`, 'info', 'ai');
        break;
      case 'show_sensors':
        addLog(`Moisture: ${sensors.soilMoisture}%, Temp: ${sensors.temperature}°C`, 'info', 'sensor');
        break;
    }
  };

  const handleCompleteTask = (taskId: string) => {
    const task = dailyTasks.find(t => t.id === taskId);
    if (!task || task.completed) return;

    setDailyTasks(prev => prev.map(t => 
      t.id === taskId ? { ...t, completed: true, completedAt: new Date().toISOString() } : t
    ));
    
    setProfile(prev => ({
      ...prev,
      xp: prev.xp + task.rewardXp,
      gold: prev.gold + task.rewardGold
    }));
    
    addLog(`Task completed: ${task.title}`, 'success', 'system');
  };

  const getSensorStatus = (value: number, type: 'moisture' | 'temp' | 'humidity' | 'water') => {
    switch (type) {
      case 'moisture':
        if (value < 30) return 'critical';
        if (value < 45 || value > 80) return 'warning';
        return 'optimal';
      case 'temp':
        if (value < 10 || value > 35) return 'critical';
        if (value < 18 || value > 30) return 'warning';
        return 'optimal';
      case 'humidity':
        if (value < 30 || value > 90) return 'warning';
        return 'optimal';
      case 'water':
        if (value < 20) return 'critical';
        if (value < 40) return 'warning';
        return 'optimal';
      default:
        return 'optimal';
    }
  };

  // Get mood indicator color
  const getMoodColor = (mood: PlantMood) => {
    const colors: Record<PlantMood, string> = {
      happy: 'text-green-400',
      thirsty: 'text-amber-400',
      hot: 'text-red-400',
      cold: 'text-blue-400',
      sick: 'text-purple-400',
      sleepy: 'text-indigo-400',
      excited: 'text-yellow-400',
      neutral: 'text-zinc-400'
    };
    return colors[mood];
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-green-500/20">
                <Leaf className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold font-display tracking-tight">SmartGrow</h1>
                <p className="text-xs text-zinc-500 font-mono">Plant Pet AI</p>
              </div>
            </div>

            {/* Plant mood indicator */}
            <div className="hidden md:flex items-center gap-4">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-800/50 ${getMoodColor(plantMood)}`}>
                <Bot className="w-4 h-4" />
                <span className="text-sm capitalize">{plant.name} is {plantMood}</span>
              </div>
            </div>

            {/* Status */}
            <div className="hidden md:flex items-center gap-6">
              <div className="flex items-center gap-2 text-sm">
                {isConnected ? (
                  <Wifi className="w-4 h-4 text-green-400" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-400" />
                )}
                <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
                  {isConnected ? 'Connected' : 'Offline'}
                </span>
              </div>
              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <RefreshCw className="w-3 h-3" />
                <span className="font-mono">Updated {lastUpdate.toLocaleTimeString()}</span>
              </div>
            </div>

            {/* Mobile menu */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 hover:bg-zinc-800 rounded-lg"
            >
              {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Column - Sensors & Charts */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Sensor Cards */}
            <section>
              <h2 className="text-sm font-mono text-zinc-500 uppercase tracking-wider mb-4">Sensor Overview</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <SensorCard
                  title="Soil Moisture"
                  value={sensors.soilMoisture}
                  unit="%"
                  icon={<Droplets className="w-5 h-5" />}
                  color="cyan"
                  percentage={sensors.soilMoisture}
                  status={getSensorStatus(sensors.soilMoisture, 'moisture')}
                  trend={sensors.soilMoisture > 50 ? 'stable' : 'down'}
                />
                <SensorCard
                  title="Temperature"
                  value={sensors.temperature}
                  unit="C"
                  icon={<Thermometer className="w-5 h-5" />}
                  color="amber"
                  percentage={((sensors.temperature - 10) / 30) * 100}
                  status={getSensorStatus(sensors.temperature, 'temp')}
                />
                <SensorCard
                  title="Humidity"
                  value={sensors.humidity}
                  unit="%"
                  icon={<Wind className="w-5 h-5" />}
                  color="blue"
                  percentage={sensors.humidity}
                  status={getSensorStatus(sensors.humidity, 'humidity')}
                />
                <SensorCard
                  title="Water Tank"
                  value={sensors.waterLevel}
                  unit="%"
                  icon={<Gauge className="w-5 h-5" />}
                  color="green"
                  percentage={sensors.waterLevel}
                  status={getSensorStatus(sensors.waterLevel, 'water')}
                />
              </div>
            </section>

            {/* Charts */}
            <section>
              <h2 className="text-sm font-mono text-zinc-500 uppercase tracking-wider mb-4">24-Hour History</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SensorChart
                  data={sensorHistory}
                  dataKey="soilMoisture"
                  title="Soil Moisture"
                  color="#06b6d4"
                  unit="%"
                />
                <SensorChart
                  data={sensorHistory}
                  dataKey="temperature"
                  title="Temperature"
                  color="#f59e0b"
                  unit="C"
                />
              </div>
            </section>

            {/* Control Panel & AI Assistant */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <ControlPanel
                controls={controls}
                onTogglePump={handleTogglePump}
                onToggleUV={handleToggleUV}
                onToggleAutoWatering={handleToggleAutoWatering}
                onToggleAutoLighting={handleToggleAutoLighting}
                isWatering={isWatering}
              />
              <AIAssistant
                recommendations={recommendations}
                sensors={sensors}
                plantName={plant.name}
                onDismiss={handleDismissRecommendation}
                onAction={handleAIAction}
              />
            </div>

            {/* System Logs */}
            <SystemLogs logs={logs} />
          </div>

          {/* Right Column - Plant & Game */}
          <div className="lg:col-span-4 space-y-6">
            {/* 3D Plant Visualization */}
            <section className="card-glass p-1">
              <div className="relative h-[300px] rounded-xl overflow-hidden">
                <Plant3D
                  growthStage={plant.growthStage as 'seed' | 'sprout' | 'seedling' | 'vegetative' | 'flowering' | 'mature'}
                  moisture={sensors.soilMoisture}
                  temperature={sensors.temperature}
                  health={plant.health}
                  isWatering={isWatering}
                  lightOn={controls.uvLightActive}
                  mood={plantMood}
                />
              </div>
            </section>
            
            <PlantStatus plant={plant} />
            <GamePanel
              profile={profile}
              achievements={achievements}
              dailyTasks={dailyTasks}
              onCompleteTask={handleCompleteTask}
            />
          </div>
        </div>
      </main>

      {/* Plant Pet Chat Button */}
      <PlantPetChat
        plant={plant}
        sensors={sensors}
        onAction={handlePlantAction}
      />

      {/* Footer */}
      <footer className="border-t border-zinc-900 mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-zinc-500">
            <div className="flex items-center gap-2">
              <Leaf className="w-4 h-4 text-green-500" />
              <span>SmartGrow Plant Pet</span>
              <span className="text-zinc-700">|</span>
              <span>Infomatrix Ukraine 2026</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="font-mono text-xs">Raspberry Pi 4 + Local AI</span>
              <span className="text-zinc-700">|</span>
              <span className="font-mono text-xs">v2.0.0</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
