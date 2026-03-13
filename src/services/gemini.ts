import { GoogleGenAI, Type } from "@google/genai";
import type { SensorData, AIRecommendation, DailyTask } from "../types";

const ai = new GoogleGenAI({ apiKey: import.meta.env.VITE_GEMINI_API_KEY || "" });

export async function analyzeGreenhouseStatus(
  sensors: SensorData,
  plantName: string,
  plantHealth: number
): Promise<AIRecommendation[]> {
  const model = ai.models.generateContent({
    model: "gemini-2.0-flash",
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          recommendations: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                type: { type: Type.STRING, enum: ["warning", "suggestion", "success"] },
                message: { type: Type.STRING },
                action: { type: Type.STRING, enum: ["water", "light_on", "light_off", "check_plant", "none"] }
              },
              required: ["type", "message", "action"]
            }
          }
        },
        required: ["recommendations"]
      }
    },
    contents: `You are SmartGrow AI - an intelligent greenhouse assistant. Analyze the following sensor data and provide actionable recommendations.

Current Sensor Readings:
- Soil Moisture: ${sensors.soilMoisture}%
- Temperature: ${sensors.temperature}°C
- Humidity: ${sensors.humidity}%
- Water Level in Tank: ${sensors.waterLevel}%
- Light Level: ${sensors.lightLevel} lux

Plant Status:
- Name: ${plantName}
- Health: ${plantHealth}%

Rules:
- If soil moisture < 30%, recommend watering (type: "warning")
- If soil moisture > 80%, warn about overwatering
- If temperature > 35°C or < 10°C, warn about temperature stress
- If light level < 200 lux and it's daytime (assume 7:00-22:00), suggest turning on UV light
- If plant health is good and conditions are optimal, give positive feedback (type: "success")
- Provide 1-3 recommendations maximum
- Keep messages concise and friendly, like a helpful gardening companion`
  });

  const response = await model;
  try {
    const data = JSON.parse(response.text || '{"recommendations":[]}');
    return data.recommendations.map((rec: any, idx: number) => ({
      id: `ai-rec-${Date.now()}-${idx}`,
      ...rec,
      action: rec.action === "none" ? undefined : rec.action,
      timestamp: new Date().toISOString()
    }));
  } catch {
    return [];
  }
}

export async function generateDailyTasks(
  sensors: SensorData,
  plantName: string,
  completedTasksToday: number
): Promise<Omit<DailyTask, 'id' | 'uid' | 'createdAt'>[]> {
  const model = ai.models.generateContent({
    model: "gemini-2.0-flash",
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          tasks: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                title: { type: Type.STRING },
                description: { type: Type.STRING },
                type: { type: Type.STRING, enum: ["water", "check_sensors", "adjust_light", "photo_check", "ai_consultation"] },
                rewardXp: { type: Type.NUMBER },
                rewardGold: { type: Type.NUMBER }
              },
              required: ["title", "description", "type", "rewardXp", "rewardGold"]
            }
          }
        },
        required: ["tasks"]
      }
    },
    contents: `Generate 3-4 daily greenhouse care tasks for the player. Make them feel like quests in a plant care game.

Current conditions:
- Soil Moisture: ${sensors.soilMoisture}%
- Plant: ${plantName}
- Tasks completed today: ${completedTasksToday}

Task types and typical rewards:
- "water": Water the plant (15-30 XP, 5-15 gold)
- "check_sensors": Check all sensor readings (10-20 XP, 5-10 gold)
- "adjust_light": Optimize lighting conditions (20-40 XP, 10-20 gold)
- "photo_check": Take a photo to verify plant health (25-50 XP, 15-25 gold)
- "ai_consultation": Ask AI for plant care advice (15-25 XP, 10-15 gold)

Make task titles fun and game-like (e.g., "The Morning Hydration Ritual", "Light Guardian Duty").
Keep descriptions encouraging and plant-care focused.`
  });

  const response = await model;
  try {
    const data = JSON.parse(response.text || '{"tasks":[]}');
    return data.tasks.map((task: any) => ({
      ...task,
      completed: false
    }));
  } catch {
    return [];
  }
}

export async function verifyPlantPhoto(
  base64Image: string,
  taskDescription: string
): Promise<{ verified: boolean; feedback: string; healthScore?: number }> {
  const model = ai.models.generateContent({
    model: "gemini-2.0-flash",
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          verified: { type: Type.BOOLEAN },
          feedback: { type: Type.STRING },
          healthScore: { type: Type.NUMBER }
        },
        required: ["verified", "feedback"]
      }
    },
    contents: [
      {
        text: `You are SmartGrow AI verifying a plant care task. The player claims to have completed: "${taskDescription}".
        
Analyze the image to:
1. Verify if the photo shows a plant/greenhouse that matches the task
2. Assess the visible plant health (0-100 score)
3. Provide encouraging feedback in a game-like tone

If verified, congratulate them! If not, gently explain what's needed.`
      },
      {
        inlineData: {
          mimeType: "image/jpeg",
          data: base64Image.split(',')[1] || base64Image
        }
      }
    ]
  });

  const response = await model;
  try {
    return JSON.parse(response.text || '{"verified":false,"feedback":"Could not analyze image"}');
  } catch {
    return { verified: false, feedback: "Could not analyze image" };
  }
}

export async function getPlantCareAdvice(
  question: string,
  plantName: string,
  sensors: SensorData
): Promise<string> {
  const model = ai.models.generateContent({
    model: "gemini-2.0-flash",
    contents: `You are SmartGrow AI, a friendly and knowledgeable greenhouse assistant. 
    
The player asks: "${question}"

Context:
- Plant: ${plantName}
- Current soil moisture: ${sensors.soilMoisture}%
- Temperature: ${sensors.temperature}°C
- Humidity: ${sensors.humidity}%
- Light level: ${sensors.lightLevel} lux

Provide helpful, concise advice (2-3 sentences max). Be encouraging and use a friendly tone.`
  });

  const response = await model;
  return response.text || "I'm having trouble thinking right now. Try asking again!";
}
