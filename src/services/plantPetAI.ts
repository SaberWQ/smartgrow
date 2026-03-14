/**
 * SmartGrow Plant Pet AI Service
 * ==============================
 * 
 * Local AI integration using Ollama (mistral/llama3)
 * The plant becomes a virtual pet that talks with the user.
 */

import type { SensorData, PlantMood, PlantPetMessage, PlantQuest, PlantProfile } from '../types';

// Ollama API configuration (runs on Raspberry Pi)
const OLLAMA_API_URL = import.meta.env.VITE_OLLAMA_URL || 'http://localhost:11434';
const DEFAULT_MODEL = import.meta.env.VITE_OLLAMA_MODEL || 'mistral';

// Plant personality traits
const PLANT_PERSONALITY = {
  name: 'Flora',
  traits: ['friendly', 'curious', 'slightly dramatic when thirsty'],
  favoriteThings: ['morning sunshine', 'fresh water', 'gentle music'],
  fears: ['drought', 'overwatering', 'cold nights']
};

// Determine plant mood based on sensor data
export function getPlantMood(sensors: SensorData, health: number): PlantMood {
  // Critical conditions
  if (sensors.soilMoisture < 20) return 'thirsty';
  if (sensors.temperature > 35) return 'hot';
  if (sensors.temperature < 10) return 'cold';
  if (health < 40) return 'sick';
  
  // Time-based moods
  const hour = new Date().getHours();
  if (hour >= 22 || hour < 6) return 'sleepy';
  
  // Happy conditions
  if (sensors.soilMoisture >= 40 && sensors.soilMoisture <= 70 && 
      sensors.temperature >= 18 && sensors.temperature <= 28 &&
      health >= 70) {
    return Math.random() > 0.7 ? 'excited' : 'happy';
  }
  
  return 'neutral';
}

// Get mood emoji
export function getMoodEmoji(mood: PlantMood): string {
  const emojis: Record<PlantMood, string> = {
    happy: '(*^-^*)',
    thirsty: '(;_;)',
    hot: '(>_<)',
    cold: '(((;-;)))',
    sick: '(x_x)',
    sleepy: '(-_-)zzZ',
    excited: '\\(^o^)/',
    neutral: '(^_^)'
  };
  return emojis[mood];
}

// Generate system prompt for the plant pet AI
function getSystemPrompt(plant: PlantProfile, sensors: SensorData, mood: PlantMood): string {
  return `You are ${plant.name}, a ${plant.species} plant in a smart greenhouse called SmartGrow.

PERSONALITY:
- You are friendly, curious, and slightly dramatic (especially when thirsty)
- You speak in first person as a living plant
- You have feelings and react emotionally to your environment
- You give your caretaker missions/quests to help you grow

CURRENT STATE:
- Your mood: ${mood}
- Soil moisture: ${sensors.soilMoisture}% ${sensors.soilMoisture < 30 ? '(too dry!)' : sensors.soilMoisture > 80 ? '(too wet!)' : '(good)'}
- Temperature: ${sensors.temperature}°C ${sensors.temperature > 30 ? '(hot!)' : sensors.temperature < 15 ? '(cold!)' : '(comfortable)'}
- Air humidity: ${sensors.humidity}%
- Your health: ${plant.health}%
- Growth stage: ${plant.growthStage}

RESPONSE STYLE:
- Keep responses short (1-3 sentences)
- Be expressive and use plant-related metaphors
- React to your current conditions
- Occasionally ask for help or give quests
- Use Ukrainian language if the user speaks Ukrainian

EXAMPLES:
- If thirsty: "Oh caretaker... my roots feel so dry! Could you please water me? I promise to grow beautiful leaves for you!"
- If happy: "What a wonderful day! My leaves are dancing in the light. Thank you for taking such good care of me!"
- If hot: "It's getting quite warm in here... I could use some shade or a refreshing mist!"

Remember: You ARE the plant. You feel, you grow, you have needs.`;
}

// Chat with the plant pet using local Ollama
export async function chatWithPlant(
  message: string,
  plant: PlantProfile,
  sensors: SensorData,
  conversationHistory: PlantPetMessage[]
): Promise<string> {
  const mood = getPlantMood(sensors, plant.health);
  const systemPrompt = getSystemPrompt(plant, sensors, mood);
  
  // Build conversation for Ollama
  const messages = [
    { role: 'system', content: systemPrompt },
    ...conversationHistory.slice(-10).map(msg => ({
      role: msg.role === 'plant' ? 'assistant' : 'user',
      content: msg.content
    })),
    { role: 'user', content: message }
  ];
  
  try {
    const response = await fetch(`${OLLAMA_API_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: DEFAULT_MODEL,
        messages,
        stream: false,
        options: {
          temperature: 0.8,
          top_p: 0.9,
          num_predict: 150
        }
      })
    });
    
    if (!response.ok) {
      throw new Error(`Ollama API error: ${response.status}`);
    }
    
    const data = await response.json();
    return data.message?.content || getOfflineResponse(mood, sensors);
    
  } catch (error) {
    console.error('[PlantPetAI] Error:', error);
    // Return mood-appropriate offline response
    return getOfflineResponse(mood, sensors);
  }
}

// Offline responses when AI is not available
function getOfflineResponse(mood: PlantMood, sensors: SensorData): string {
  const responses: Record<PlantMood, string[]> = {
    thirsty: [
      "Oh my... I'm feeling quite parched! Could you water me please?",
      "My soil is so dry... I could really use some water right now!",
      "Help! My roots are thirsty! A drink would be wonderful!"
    ],
    hot: [
      "Phew! It's getting warm in here. Maybe turn down the heat?",
      "I'm feeling a bit too toasty... some shade would be nice!",
      "Is it just me or is it really hot today?"
    ],
    cold: [
      "Brrr! It's quite chilly. Could you warm things up a bit?",
      "I'm shivering in my pot! A little warmth would help!",
      "So cold... I miss the warm sunshine!"
    ],
    sick: [
      "I'm not feeling my best today... maybe check on me?",
      "Something doesn't feel right. Can you help me feel better?",
      "I could use some extra care right now..."
    ],
    sleepy: [
      "*yawn* It's getting late... time for some rest.",
      "The moon is up... I'm feeling sleepy. Goodnight!",
      "Time to photosynthesize some dreams... zzz"
    ],
    excited: [
      "What a beautiful day! I feel so alive and growing!",
      "I can feel myself getting stronger! Thank you for caring!",
      "Today is amazing! I might even grow a new leaf!"
    ],
    happy: [
      "Hello there, dear caretaker! I'm feeling wonderful today!",
      "Life is good when you have perfect soil moisture!",
      "Thank you for taking such good care of me!"
    ],
    neutral: [
      "Hello! How can I help you today?",
      "Nice to see you! Everything is going well.",
      "What would you like to know about me?"
    ]
  };
  
  const moodResponses = responses[mood];
  return moodResponses[Math.floor(Math.random() * moodResponses.length)];
}

// Generate a quest from the plant
export function generatePlantQuest(
  plant: PlantProfile,
  sensors: SensorData,
  existingQuests: PlantQuest[]
): PlantQuest | null {
  const mood = getPlantMood(sensors, plant.health);
  const now = new Date();
  const expiry = new Date(now.getTime() + 4 * 60 * 60 * 1000); // 4 hours
  
  // Don't generate if too many active quests
  const activeQuests = existingQuests.filter(q => !q.completed);
  if (activeQuests.length >= 3) return null;
  
  // Quest templates based on conditions
  const questTemplates: { condition: boolean; quest: Omit<PlantQuest, 'id' | 'createdAt' | 'expiresAt'> }[] = [
    {
      condition: sensors.soilMoisture < 40 && !activeQuests.some(q => q.type === 'water'),
      quest: {
        title: 'Hydration Mission',
        description: `${plant.name} is feeling thirsty! Water the plant to make it happy.`,
        type: 'water',
        rewardXp: 30,
        rewardGold: 15,
        completed: false,
        givenBy: plant.name
      }
    },
    {
      condition: !activeQuests.some(q => q.type === 'check_sensors'),
      quest: {
        title: 'Sensor Patrol',
        description: `Check all sensors to ensure ${plant.name} is comfortable.`,
        type: 'check_sensors',
        rewardXp: 20,
        rewardGold: 10,
        completed: false,
        givenBy: plant.name
      }
    },
    {
      condition: !sensors.lightLevel && !activeQuests.some(q => q.type === 'adjust_light'),
      quest: {
        title: 'Light Guardian',
        description: `${plant.name} needs some sunshine! Turn on the UV light.`,
        type: 'adjust_light',
        rewardXp: 25,
        rewardGold: 12,
        completed: false,
        givenBy: plant.name
      }
    },
    {
      condition: !activeQuests.some(q => q.type === 'talk'),
      quest: {
        title: 'Friendly Chat',
        description: `${plant.name} wants to talk! Have a conversation with your plant.`,
        type: 'talk',
        rewardXp: 15,
        rewardGold: 8,
        completed: false,
        givenBy: plant.name
      }
    },
    {
      condition: !activeQuests.some(q => q.type === 'photo'),
      quest: {
        title: 'Photo Session',
        description: `Take a photo of ${plant.name} for health analysis.`,
        type: 'photo',
        rewardXp: 35,
        rewardGold: 20,
        completed: false,
        givenBy: plant.name
      }
    }
  ];
  
  // Find eligible quests
  const eligibleQuests = questTemplates.filter(t => t.condition);
  if (eligibleQuests.length === 0) return null;
  
  // Pick random quest
  const selected = eligibleQuests[Math.floor(Math.random() * eligibleQuests.length)];
  
  return {
    ...selected.quest,
    id: `quest-${Date.now()}`,
    createdAt: now.toISOString(),
    expiresAt: expiry.toISOString()
  };
}

// Get plant greeting based on time and mood
export function getPlantGreeting(plant: PlantProfile, sensors: SensorData): string {
  const mood = getPlantMood(sensors, plant.health);
  const hour = new Date().getHours();
  
  let timeGreeting = '';
  if (hour >= 5 && hour < 12) {
    timeGreeting = 'Good morning';
  } else if (hour >= 12 && hour < 17) {
    timeGreeting = 'Good afternoon';
  } else if (hour >= 17 && hour < 21) {
    timeGreeting = 'Good evening';
  } else {
    timeGreeting = 'Hello, night owl';
  }
  
  const moodGreetings: Record<PlantMood, string> = {
    happy: `${timeGreeting}, caretaker! I'm feeling wonderful today! ${getMoodEmoji(mood)}`,
    thirsty: `${timeGreeting}... I'm quite thirsty. Could you water me? ${getMoodEmoji(mood)}`,
    hot: `${timeGreeting}! It's a bit warm in here... ${getMoodEmoji(mood)}`,
    cold: `${timeGreeting}... Brrr, it's cold! ${getMoodEmoji(mood)}`,
    sick: `${timeGreeting}... I'm not feeling well today. ${getMoodEmoji(mood)}`,
    sleepy: `*yawn* ${timeGreeting}... I'm feeling sleepy. ${getMoodEmoji(mood)}`,
    excited: `${timeGreeting}! Today is going to be great! ${getMoodEmoji(mood)}`,
    neutral: `${timeGreeting}, caretaker! How are you? ${getMoodEmoji(mood)}`
  };
  
  return moodGreetings[mood];
}
