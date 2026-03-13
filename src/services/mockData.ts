import type { SensorData, Achievement, SystemLog, WateringEvent, AIRecommendation } from "../types";

// Simulate sensor data with realistic variations
export function generateSensorData(): SensorData {
  const baseTime = Date.now();
  const hourOfDay = new Date().getHours();
  
  // Simulate day/night light cycle
  const isDaytime = hourOfDay >= 7 && hourOfDay <= 22;
  const baseLightLevel = isDaytime ? 600 : 50;
  
  return {
    soilMoisture: Math.round(45 + Math.random() * 30), // 45-75%
    temperature: Math.round((22 + Math.random() * 6) * 10) / 10, // 22-28°C
    humidity: Math.round(55 + Math.random() * 20), // 55-75%
    waterLevel: Math.round(60 + Math.random() * 30), // 60-90%
    lightLevel: Math.round(baseLightLevel + Math.random() * 200),
    timestamp: new Date(baseTime).toISOString()
  };
}

// Historical sensor data for charts
export function generateSensorHistory(hours: number = 24): SensorData[] {
  const history: SensorData[] = [];
  const now = Date.now();
  
  for (let i = hours; i >= 0; i--) {
    const timestamp = new Date(now - i * 60 * 60 * 1000);
    const hour = timestamp.getHours();
    const isDaytime = hour >= 7 && hour <= 22;
    
    history.push({
      soilMoisture: Math.round(40 + Math.sin(i / 4) * 15 + Math.random() * 10),
      temperature: Math.round((23 + Math.sin(i / 6) * 3 + Math.random() * 2) * 10) / 10,
      humidity: Math.round(60 + Math.cos(i / 5) * 10 + Math.random() * 5),
      waterLevel: Math.round(70 - (i * 0.5) + Math.random() * 5),
      lightLevel: Math.round((isDaytime ? 500 : 20) + Math.random() * 200),
      timestamp: timestamp.toISOString()
    });
  }
  
  return history;
}

// All available achievements
export const ALL_ACHIEVEMENTS: Achievement[] = [
  {
    id: 'first_watering',
    name: 'First Drop',
    description: 'Complete your first watering',
    icon: '💧',
    rewardXp: 50,
    rewardGold: 25
  },
  {
    id: 'perfect_moisture',
    name: 'Perfect Balance',
    description: 'Maintain optimal soil moisture for 24 hours',
    icon: '⚖️',
    rewardXp: 100,
    rewardGold: 50
  },
  {
    id: 'efficient_water_use',
    name: 'Water Sage',
    description: 'Use auto-watering efficiently for 7 days',
    icon: '🌊',
    rewardXp: 150,
    rewardGold: 75
  },
  {
    id: 'green_thumb',
    name: 'Green Thumb',
    description: 'Reach 100% plant health',
    icon: '🌿',
    rewardXp: 200,
    rewardGold: 100
  },
  {
    id: 'light_master',
    name: 'Light Master',
    description: 'Optimize UV lighting for a full growth cycle',
    icon: '☀️',
    rewardXp: 175,
    rewardGold: 85
  },
  {
    id: 'streak_7',
    name: 'Week Warrior',
    description: 'Maintain a 7-day care streak',
    icon: '🔥',
    rewardXp: 250,
    rewardGold: 125
  },
  {
    id: 'streak_30',
    name: 'Monthly Master',
    description: 'Maintain a 30-day care streak',
    icon: '👑',
    rewardXp: 500,
    rewardGold: 250
  },
  {
    id: 'plant_whisperer',
    name: 'Plant Whisperer',
    description: 'Successfully grow a plant to maturity',
    icon: '🌸',
    rewardXp: 1000,
    rewardGold: 500
  },
  {
    id: 'automation_expert',
    name: 'Automation Expert',
    description: 'Set up fully automated greenhouse care',
    icon: '🤖',
    rewardXp: 300,
    rewardGold: 150
  }
];

// Generate mock system logs
export function generateSystemLogs(count: number = 10): SystemLog[] {
  const logTemplates: Array<{ type: SystemLog['type']; message: string; source: SystemLog['source'] }> = [
    { type: 'info', message: 'Sensor readings updated', source: 'sensor' },
    { type: 'success', message: 'Watering cycle completed', source: 'pump' },
    { type: 'info', message: 'UV light activated', source: 'light' },
    { type: 'info', message: 'UV light deactivated', source: 'light' },
    { type: 'success', message: 'AI analysis complete', source: 'ai' },
    { type: 'warning', message: 'Soil moisture below threshold', source: 'sensor' },
    { type: 'warning', message: 'Water tank level low', source: 'sensor' },
    { type: 'info', message: 'Auto-watering triggered', source: 'system' },
    { type: 'success', message: 'Plant health check passed', source: 'ai' },
    { type: 'info', message: 'Day session started', source: 'system' }
  ];
  
  const logs: SystemLog[] = [];
  const now = Date.now();
  
  for (let i = 0; i < count; i++) {
    const template = logTemplates[Math.floor(Math.random() * logTemplates.length)];
    logs.push({
      id: `log-${now}-${i}`,
      ...template,
      timestamp: new Date(now - i * 15 * 60 * 1000).toISOString() // Every 15 minutes
    });
  }
  
  return logs;
}

// Generate mock watering events
export function generateWateringEvents(count: number = 5): WateringEvent[] {
  const events: WateringEvent[] = [];
  const now = Date.now();
  
  for (let i = 0; i < count; i++) {
    const moistureBefore = Math.round(25 + Math.random() * 15);
    events.push({
      id: `water-${now}-${i}`,
      uid: 'demo-user',
      timestamp: new Date(now - i * 8 * 60 * 60 * 1000).toISOString(), // Every 8 hours
      duration: Math.round(10 + Math.random() * 20),
      moistureBefore,
      moistureAfter: Math.round(moistureBefore + 30 + Math.random() * 20),
      triggeredBy: Math.random() > 0.5 ? 'auto' : 'manual'
    });
  }
  
  return events;
}

// Default AI recommendations
export function getDefaultRecommendations(sensors: SensorData): AIRecommendation[] {
  const recommendations: AIRecommendation[] = [];
  
  if (sensors.soilMoisture < 35) {
    recommendations.push({
      id: `rec-${Date.now()}-1`,
      type: 'warning',
      message: `Soil moisture is at ${sensors.soilMoisture}%. Your plant needs water soon!`,
      action: 'water',
      timestamp: new Date().toISOString()
    });
  }
  
  if (sensors.lightLevel < 200) {
    recommendations.push({
      id: `rec-${Date.now()}-2`,
      type: 'suggestion',
      message: 'Light levels are low. Consider turning on the UV grow light.',
      action: 'light_on',
      timestamp: new Date().toISOString()
    });
  }
  
  if (sensors.soilMoisture >= 50 && sensors.soilMoisture <= 70 && sensors.temperature >= 20 && sensors.temperature <= 28) {
    recommendations.push({
      id: `rec-${Date.now()}-3`,
      type: 'success',
      message: 'Excellent conditions! Your plant is thriving in this environment.',
      timestamp: new Date().toISOString()
    });
  }
  
  return recommendations;
}

// Calculate XP needed for next level
export function calculateXpForLevel(level: number): number {
  return Math.floor(100 * Math.pow(1.5, level - 1));
}

// Calculate level from total XP
export function calculateLevelFromXp(totalXp: number): { level: number; currentLevelXp: number; nextLevelXp: number } {
  let level = 1;
  let xpAccumulated = 0;
  
  while (xpAccumulated + calculateXpForLevel(level) <= totalXp) {
    xpAccumulated += calculateXpForLevel(level);
    level++;
  }
  
  return {
    level,
    currentLevelXp: totalXp - xpAccumulated,
    nextLevelXp: calculateXpForLevel(level)
  };
}

// Plant growth stages with progress thresholds
export const GROWTH_STAGES = {
  seed: { min: 0, max: 10, name: 'Seed', icon: '🌰' },
  sprout: { min: 10, max: 25, name: 'Sprout', icon: '🌱' },
  seedling: { min: 25, max: 50, name: 'Seedling', icon: '🌿' },
  vegetative: { min: 50, max: 75, name: 'Vegetative', icon: '🪴' },
  flowering: { min: 75, max: 90, name: 'Flowering', icon: '🌸' },
  mature: { min: 90, max: 100, name: 'Mature', icon: '🌺' }
} as const;

export function getGrowthStage(progress: number): keyof typeof GROWTH_STAGES {
  if (progress < 10) return 'seed';
  if (progress < 25) return 'sprout';
  if (progress < 50) return 'seedling';
  if (progress < 75) return 'vegetative';
  if (progress < 90) return 'flowering';
  return 'mature';
}
