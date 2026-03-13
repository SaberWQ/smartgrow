// SmartGrow Types

export interface UserProfile {
  uid: string;
  displayName: string;
  email: string;
  photoURL?: string;
  level: number;
  xp: number;
  gold: number;
  totalWaterings: number;
  totalUVSessions: number;
  streak: number;
  lastActiveDate?: string;
}

export interface SensorData {
  soilMoisture: number;       // 0-100%
  temperature: number;        // Celsius
  humidity: number;           // 0-100%
  waterLevel: number;         // 0-100%
  lightLevel: number;         // 0-1000 lux
  timestamp: string;
}

export interface GreenhouseControls {
  pumpActive: boolean;
  uvLightActive: boolean;
  autoWateringEnabled: boolean;
  autoLightingEnabled: boolean;
  wateringThreshold: number;  // moisture % below which to water
  lightingSchedule: {
    startHour: number;
    endHour: number;
  };
}

export interface PlantProfile {
  id: string;
  uid: string;
  name: string;
  species: string;
  plantedAt: string;
  health: number;             // 0-100
  growthStage: 'seed' | 'sprout' | 'seedling' | 'vegetative' | 'flowering' | 'mature';
  growthProgress: number;     // 0-100 within current stage
  totalWaterings: number;
  lastWateredAt?: string;
  imageUrl?: string;
}

export type AchievementId = 
  | 'first_watering'
  | 'perfect_moisture'
  | 'efficient_water_use'
  | 'green_thumb'
  | 'light_master'
  | 'streak_7'
  | 'streak_30'
  | 'plant_whisperer'
  | 'automation_expert';

export interface Achievement {
  id: AchievementId;
  name: string;
  description: string;
  icon: string;
  rewardXp: number;
  rewardGold: number;
  unlockedAt?: string;
}

export interface DailyTask {
  id: string;
  uid: string;
  title: string;
  description: string;
  type: 'water' | 'check_sensors' | 'adjust_light' | 'photo_check' | 'ai_consultation';
  rewardXp: number;
  rewardGold: number;
  completed: boolean;
  createdAt: string;
  completedAt?: string;
}

export interface WateringEvent {
  id: string;
  uid: string;
  timestamp: string;
  duration: number;           // seconds
  moistureBefore: number;
  moistureAfter: number;
  triggeredBy: 'manual' | 'auto' | 'ai';
}

export interface AIRecommendation {
  id: string;
  type: 'warning' | 'suggestion' | 'success';
  message: string;
  action?: 'water' | 'light_on' | 'light_off' | 'check_plant';
  timestamp: string;
  dismissed?: boolean;
}

export interface SystemLog {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  timestamp: string;
  source: 'sensor' | 'pump' | 'light' | 'ai' | 'system';
}

export interface GameState {
  currentXp: number;
  level: number;
  gold: number;
  achievements: Achievement[];
  dailyTasks: DailyTask[];
  streak: number;
}

export interface FirestoreErrorInfo {
  error: string;
  operationType: 'create' | 'update' | 'delete' | 'list' | 'get' | 'write';
  path: string | null;
  authInfo: {
    userId?: string;
    email?: string;
    emailVerified?: boolean;
    isAnonymous?: boolean;
    tenantId?: string | null;
    providerInfo: {
      providerId: string;
      displayName: string | null;
      email: string | null;
      photoUrl: string | null;
    }[];
  };
}
