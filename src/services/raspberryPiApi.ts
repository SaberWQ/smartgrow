/**
 * SmartGrow - Raspberry Pi API Client
 * Connects web app to the Raspberry Pi greenhouse controller
 * Infomatrix Ukraine 2026
 */

// Raspberry Pi API base URL (configurable)
const PI_API_URL = import.meta.env.VITE_PI_API_URL || 'http://localhost:5000';

export interface SensorData {
  moisture: number | null;
  temperature: number | null;
  humidity: number | null;
  water_level: number | null;
  moisture_status?: string;
  temperature_status?: string;
  humidity_status?: string;
  water_status?: string;
  pump_active: boolean;
  light_active: boolean;
  light_auto_mode?: boolean;
  timestamp: number;
}

export interface SystemStatus {
  sensors: SensorData;
  pump: {
    is_running: boolean;
    cooldown_remaining: number;
    total_runtime_today: number;
    daily_usage_ml: number;
  };
  light: {
    is_on: boolean;
    auto_mode: boolean;
    schedule: {
      schedule_start: string;
      schedule_end: string;
      daily_light_hours: number;
      within_schedule: boolean;
    };
  };
  health: {
    overall_score: number;
    grade: string;
    breakdown: Record<string, {
      value: number;
      score: number;
      status: string;
    }>;
  };
  timestamp: number;
}

export interface GameStats {
  level: number;
  xp: number;
  xp_for_next_level: number;
  gold: number;
  streak: number;
  plant_stage: number;
  plant_stage_name: string;
  plant_health: number;
  achievements: string[];
  daily_tasks_completed: string[];
}

export interface Recommendation {
  priority: 'high' | 'medium' | 'low';
  category: string;
  title: string;
  message: string;
  action: string;
}

export interface HourlyData {
  hours: string[];
  moisture: (number | null)[];
  temperature: (number | null)[];
  humidity: (number | null)[];
  water_level: (number | null)[];
}

export interface WateringPrediction {
  needs_watering_now: boolean;
  current_moisture: number;
  threshold: number;
  hours_until_needed?: number;
  predicted_time?: string;
  urgency?: 'immediate' | 'soon' | 'scheduled' | 'not_urgent';
  confidence?: string;
}

export interface TrendData {
  direction: 'rising' | 'falling' | 'stable';
  slope_per_hour: number;
  r_squared: number;
  current_value: number;
  predicted_3h: number;
  confidence: 'high' | 'medium' | 'low';
}

// WebSocket connection
let wsConnection: WebSocket | null = null;
let wsReconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

/**
 * Generic API fetch wrapper
 */
async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${PI_API_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data.success && data.error) {
      throw new Error(data.error);
    }
    
    return data;
  } catch (error) {
    console.error(`[SmartGrow API] Error fetching ${endpoint}:`, error);
    throw error;
  }
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; version: string }> {
  return apiFetch('/api/health');
}

/**
 * Get current sensor readings
 */
export async function getSensors(): Promise<SensorData> {
  const response = await apiFetch<{ success: boolean; data: SensorData }>('/api/sensors');
  return response.data;
}

/**
 * Get sensor history for charts
 */
export async function getSensorHistory(hours: number = 24): Promise<HourlyData> {
  const response = await apiFetch<{ success: boolean; data: HourlyData }>(
    `/api/sensors/history?hours=${hours}`
  );
  return response.data;
}

/**
 * Get full system status
 */
export async function getSystemStatus(): Promise<SystemStatus> {
  const response = await apiFetch<{ success: boolean; data: SystemStatus }>('/api/status');
  return response.data;
}

/**
 * Trigger watering
 */
export async function waterPlant(duration?: number): Promise<{
  success: boolean;
  duration_seconds?: number;
  water_dispensed_ml?: number;
  message?: string;
}> {
  const response = await apiFetch<{ success: boolean; data: any }>('/api/water', {
    method: 'POST',
    body: JSON.stringify({ duration }),
  });
  return response.data;
}

/**
 * Toggle auto-watering
 */
export async function setAutoWatering(enabled: boolean): Promise<void> {
  await apiFetch('/api/water/auto', {
    method: 'POST',
    body: JSON.stringify({ enabled }),
  });
}

/**
 * Control UV grow light
 */
export async function controlLight(state: 'on' | 'off' | 'toggle'): Promise<{
  success: boolean;
  is_on: boolean;
  message?: string;
}> {
  const response = await apiFetch<{ success: boolean; data: any }>('/api/light', {
    method: 'POST',
    body: JSON.stringify({ state }),
  });
  return response.data;
}

/**
 * Toggle auto-lighting
 */
export async function setAutoLight(enabled: boolean): Promise<void> {
  await apiFetch('/api/light/auto', {
    method: 'POST',
    body: JSON.stringify({ enabled }),
  });
}

/**
 * Set light schedule
 */
export async function setLightSchedule(startHour: number, endHour: number): Promise<void> {
  await apiFetch('/api/light/schedule', {
    method: 'POST',
    body: JSON.stringify({ start_hour: startHour, end_hour: endHour }),
  });
}

/**
 * Get analytics statistics
 */
export async function getAnalytics(hours: number = 24): Promise<{
  statistics: Record<string, {
    current: number;
    mean: number;
    min: number;
    max: number;
    std: number;
  }>;
  trends: Record<string, TrendData>;
}> {
  const response = await apiFetch<{ success: boolean; statistics: any; trends: any }>(
    `/api/analytics/stats?hours=${hours}`
  );
  return {
    statistics: response.statistics,
    trends: response.trends,
  };
}

/**
 * Get watering prediction
 */
export async function getWateringPrediction(): Promise<WateringPrediction> {
  const response = await apiFetch<{ success: boolean; data: WateringPrediction }>(
    '/api/analytics/predictions'
  );
  return response.data;
}

/**
 * Get AI recommendations
 */
export async function getRecommendations(): Promise<Recommendation[]> {
  const response = await apiFetch<{ success: boolean; data: Recommendation[] }>(
    '/api/recommendations'
  );
  return response.data;
}

/**
 * Get game statistics
 */
export async function getGameStats(): Promise<GameStats> {
  const response = await apiFetch<{ success: boolean; data: GameStats }>('/api/game/stats');
  return response.data;
}

/**
 * Get recent events
 */
export async function getEvents(limit: number = 50): Promise<Array<{
  type: string;
  description: string;
  timestamp: number;
}>> {
  const response = await apiFetch<{ success: boolean; data: any[] }>(
    `/api/events?limit=${limit}`
  );
  return response.data;
}

/**
 * WebSocket connection for real-time updates
 */
export function connectWebSocket(
  onSensors: (data: SensorData) => void,
  onEvent: (event: { type: string; data: any; timestamp: number }) => void,
  onError?: (error: Error) => void
): () => void {
  const wsUrl = PI_API_URL.replace('http://', 'ws://').replace('https://', 'wss://');
  
  function connect() {
    try {
      wsConnection = new WebSocket(wsUrl);
      
      wsConnection.onopen = () => {
        console.log('[SmartGrow WS] Connected');
        wsReconnectAttempts = 0;
      };
      
      wsConnection.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.sensors) {
            onSensors(message);
          } else if (message.type === 'sensors') {
            onSensors(message.data || message);
          } else if (message.type) {
            onEvent(message);
          }
        } catch (error) {
          console.error('[SmartGrow WS] Parse error:', error);
        }
      };
      
      wsConnection.onerror = (error) => {
        console.error('[SmartGrow WS] Error:', error);
        onError?.(new Error('WebSocket connection error'));
      };
      
      wsConnection.onclose = () => {
        console.log('[SmartGrow WS] Disconnected');
        
        // Attempt reconnection
        if (wsReconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          wsReconnectAttempts++;
          const delay = Math.min(1000 * Math.pow(2, wsReconnectAttempts), 30000);
          console.log(`[SmartGrow WS] Reconnecting in ${delay}ms...`);
          setTimeout(connect, delay);
        }
      };
    } catch (error) {
      console.error('[SmartGrow WS] Connection failed:', error);
      onError?.(error as Error);
    }
  }
  
  connect();
  
  // Return cleanup function
  return () => {
    if (wsConnection) {
      wsConnection.close();
      wsConnection = null;
    }
  };
}

/**
 * Send command via WebSocket
 */
export function sendCommand(command: string, params?: Record<string, any>): void {
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      command,
      params: params || {},
    }));
  } else {
    console.error('[SmartGrow WS] Cannot send command: not connected');
  }
}

/**
 * Check if connected to Raspberry Pi
 */
export async function isConnected(): Promise<boolean> {
  try {
    await healthCheck();
    return true;
  } catch {
    return false;
  }
}

/**
 * Get connection status
 */
export function getWebSocketStatus(): 'connected' | 'connecting' | 'disconnected' {
  if (!wsConnection) return 'disconnected';
  
  switch (wsConnection.readyState) {
    case WebSocket.OPEN:
      return 'connected';
    case WebSocket.CONNECTING:
      return 'connecting';
    default:
      return 'disconnected';
  }
}
