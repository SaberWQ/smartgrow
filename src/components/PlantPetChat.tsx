/**
 * SmartGrow Plant Pet Chat
 * ========================
 * 
 * Interactive chat with your plant pet.
 * Supports text and voice interaction.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  MessageCircle, 
  Mic, 
  MicOff, 
  Send, 
  Volume2, 
  VolumeX,
  Leaf,
  Sparkles,
  X
} from 'lucide-react';

import type { PlantPetMessage, SensorData, PlantProfile, VoiceState, PlantMood } from '../types';
import { chatWithPlant, getPlantMood, getMoodEmoji, getPlantGreeting } from '../services/plantPetAI';
import { voiceService } from '../services/voiceService';

interface PlantPetChatProps {
  plant: PlantProfile;
  sensors: SensorData;
  onAction?: (action: string) => void;
}

// Mood to color mapping
const MOOD_COLORS: Record<PlantMood, string> = {
  happy: 'from-green-500 to-emerald-500',
  thirsty: 'from-amber-500 to-orange-500',
  hot: 'from-red-500 to-orange-500',
  cold: 'from-blue-500 to-cyan-500',
  sick: 'from-purple-500 to-pink-500',
  sleepy: 'from-indigo-500 to-purple-500',
  excited: 'from-yellow-500 to-green-500',
  neutral: 'from-zinc-500 to-zinc-600'
};

export default function PlantPetChat({ plant, sensors, onAction }: PlantPetChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<PlantPetMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>({
    isListening: false,
    isSpeaking: false,
    transcript: ''
  });
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [showWelcome, setShowWelcome] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const mood = getPlantMood(sensors, plant.health);
  const moodColor = MOOD_COLORS[mood];
  
  // Setup voice callbacks
  useEffect(() => {
    voiceService.setCallbacks(
      (transcript) => {
        if (transcript) {
          handleSendMessage(transcript);
        }
      },
      (state) => {
        setVoiceState(prev => ({ ...prev, ...state }));
      }
    );
  }, []);
  
  // Show greeting when chat opens
  useEffect(() => {
    if (isOpen && showWelcome && messages.length === 0) {
      const greeting = getPlantGreeting(plant, sensors);
      const welcomeMessage: PlantPetMessage = {
        id: `msg-${Date.now()}`,
        role: 'plant',
        content: greeting,
        timestamp: new Date().toISOString(),
        mood
      };
      setMessages([welcomeMessage]);
      setShowWelcome(false);
      
      if (voiceEnabled) {
        voiceService.speak(greeting);
      }
    }
  }, [isOpen, showWelcome, plant, sensors, mood, voiceEnabled]);
  
  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleSendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return;
    
    // Add user message
    const userMessage: PlantPetMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    
    // Check for voice commands
    const command = voiceService.parseCommand(text);
    if (command && command.command !== 'chat' && onAction) {
      onAction(command.command);
    }
    
    try {
      // Get plant response
      const response = await chatWithPlant(text, plant, sensors, messages);
      
      const plantMessage: PlantPetMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'plant',
        content: response,
        timestamp: new Date().toISOString(),
        mood: getPlantMood(sensors, plant.health)
      };
      setMessages(prev => [...prev, plantMessage]);
      
      // Speak response
      if (voiceEnabled) {
        await voiceService.speak(response);
      }
      
    } catch (error) {
      console.error('[Chat] Error:', error);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, plant, sensors, messages, voiceEnabled, onAction]);
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputText);
    }
  };
  
  const toggleVoice = () => {
    if (voiceState.isListening) {
      voiceService.stopListening();
    } else {
      voiceService.startListening();
    }
  };
  
  return (
    <>
      {/* Chat Button */}
      <motion.button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full bg-gradient-to-br ${moodColor} shadow-lg shadow-green-500/30 flex items-center justify-center`}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        animate={{
          boxShadow: mood === 'thirsty' ? [
            '0 0 0 0 rgba(245, 158, 11, 0.4)',
            '0 0 0 20px rgba(245, 158, 11, 0)',
          ] : undefined
        }}
        transition={{
          duration: 1.5,
          repeat: mood === 'thirsty' ? Infinity : 0
        }}
      >
        <Leaf className="w-7 h-7 text-white" />
        {mood === 'thirsty' && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-xs text-white">!</span>
        )}
      </motion.button>
      
      {/* Chat Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          >
            <motion.div
              initial={{ y: 100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 100, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-md bg-zinc-900 rounded-2xl shadow-2xl overflow-hidden border border-zinc-800"
            >
              {/* Header */}
              <div className={`relative p-4 bg-gradient-to-r ${moodColor}`}>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                    <Leaf className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-white">{plant.name}</h3>
                    <p className="text-sm text-white/80 flex items-center gap-1">
                      <span>{getMoodEmoji(mood)}</span>
                      <span className="capitalize">{mood}</span>
                    </p>
                  </div>
                  <button
                    onClick={() => setVoiceEnabled(!voiceEnabled)}
                    className="p-2 rounded-full bg-white/20 hover:bg-white/30"
                  >
                    {voiceEnabled ? (
                      <Volume2 className="w-5 h-5 text-white" />
                    ) : (
                      <VolumeX className="w-5 h-5 text-white" />
                    )}
                  </button>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="p-2 rounded-full bg-white/20 hover:bg-white/30"
                  >
                    <X className="w-5 h-5 text-white" />
                  </button>
                </div>
                
                {/* Mood indicator */}
                {voiceState.isSpeaking && (
                  <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/30">
                    <motion.div
                      className="h-full bg-white"
                      animate={{ width: ['0%', '100%'] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                  </div>
                )}
              </div>
              
              {/* Messages */}
              <div className="h-80 overflow-y-auto p-4 space-y-3">
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                        msg.role === 'user'
                          ? 'bg-green-600 text-white rounded-br-none'
                          : 'bg-zinc-800 text-zinc-100 rounded-bl-none'
                      }`}
                    >
                      {msg.role === 'plant' && msg.mood && (
                        <span className="text-xs opacity-60 mr-1">
                          {getMoodEmoji(msg.mood)}
                        </span>
                      )}
                      {msg.content}
                    </div>
                  </motion.div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-zinc-800 rounded-2xl rounded-bl-none px-4 py-2 flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-green-400 animate-pulse" />
                      <span className="text-zinc-400">Thinking...</span>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
              
              {/* Input */}
              <div className="p-4 border-t border-zinc-800">
                {voiceState.isListening && (
                  <div className="mb-3 p-2 bg-green-900/30 rounded-lg border border-green-500/30">
                    <div className="flex items-center gap-2 text-sm text-green-400">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span>Listening: {voiceState.transcript || '...'}</span>
                    </div>
                  </div>
                )}
                
                <div className="flex items-center gap-2">
                  {voiceService.isSupported() && (
                    <button
                      onClick={toggleVoice}
                      className={`p-3 rounded-full transition-colors ${
                        voiceState.isListening
                          ? 'bg-red-500 text-white'
                          : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
                      }`}
                    >
                      {voiceState.isListening ? (
                        <MicOff className="w-5 h-5" />
                      ) : (
                        <Mic className="w-5 h-5" />
                      )}
                    </button>
                  )}
                  
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={`Talk to ${plant.name}...`}
                    className="flex-1 bg-zinc-800 border border-zinc-700 rounded-full px-4 py-2 text-white placeholder-zinc-500 focus:outline-none focus:border-green-500"
                    disabled={isLoading}
                  />
                  
                  <button
                    onClick={() => handleSendMessage(inputText)}
                    disabled={!inputText.trim() || isLoading}
                    className="p-3 rounded-full bg-green-600 text-white hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
                
                {/* Quick actions */}
                <div className="mt-3 flex flex-wrap gap-2">
                  {[
                    { label: 'How are you?', action: 'How are you feeling?' },
                    { label: 'Water me', action: 'Can you water me please?' },
                    { label: 'Health check', action: "What's your health status?" }
                  ].map((quick) => (
                    <button
                      key={quick.label}
                      onClick={() => handleSendMessage(quick.action)}
                      className="text-xs px-3 py-1 rounded-full bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white transition-colors"
                    >
                      {quick.label}
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
