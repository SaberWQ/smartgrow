/**
 * SmartGrow Voice Service
 * =======================
 * 
 * Voice interaction using Web Speech API (browser-based)
 * For Raspberry Pi: VOSK for STT, Coqui TTS for speech synthesis
 */

import type { VoiceState } from '../types';

// Raspberry Pi voice API (when available)
const VOICE_API_URL = import.meta.env.VITE_VOICE_API_URL || 'http://localhost:8001';

// Check if Web Speech API is available
const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
const speechSynthesis = window.speechSynthesis;

// Voice service class
class VoiceService {
  private recognition: any = null;
  private isListening: boolean = false;
  private onTranscript: ((text: string) => void) | null = null;
  private onStateChange: ((state: Partial<VoiceState>) => void) | null = null;
  
  constructor() {
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = 'uk-UA'; // Ukrainian
      
      this.recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0].transcript)
          .join('');
        
        if (event.results[0].isFinal && this.onTranscript) {
          this.onTranscript(transcript);
        }
        
        if (this.onStateChange) {
          this.onStateChange({ transcript });
        }
      };
      
      this.recognition.onerror = (event: any) => {
        console.error('[Voice] Recognition error:', event.error);
        this.isListening = false;
        if (this.onStateChange) {
          this.onStateChange({ 
            isListening: false, 
            error: event.error 
          });
        }
      };
      
      this.recognition.onend = () => {
        this.isListening = false;
        if (this.onStateChange) {
          this.onStateChange({ isListening: false });
        }
      };
    }
  }
  
  // Set callbacks
  setCallbacks(
    onTranscript: (text: string) => void,
    onStateChange: (state: Partial<VoiceState>) => void
  ) {
    this.onTranscript = onTranscript;
    this.onStateChange = onStateChange;
  }
  
  // Check if voice is supported
  isSupported(): boolean {
    return !!SpeechRecognition;
  }
  
  // Start listening
  startListening(): boolean {
    if (!this.recognition || this.isListening) return false;
    
    try {
      this.recognition.start();
      this.isListening = true;
      if (this.onStateChange) {
        this.onStateChange({ isListening: true, transcript: '', error: undefined });
      }
      return true;
    } catch (error) {
      console.error('[Voice] Failed to start:', error);
      return false;
    }
  }
  
  // Stop listening
  stopListening(): void {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    }
  }
  
  // Speak text using Web Speech API or Coqui TTS
  async speak(text: string, useLocalTTS: boolean = false): Promise<void> {
    if (useLocalTTS) {
      return this.speakWithCoqui(text);
    }
    
    return new Promise((resolve, reject) => {
      if (!speechSynthesis) {
        reject(new Error('Speech synthesis not supported'));
        return;
      }
      
      // Cancel any ongoing speech
      speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'uk-UA'; // Ukrainian
      utterance.rate = 0.9;
      utterance.pitch = 1.1; // Slightly higher for plant character
      
      // Find Ukrainian voice if available
      const voices = speechSynthesis.getVoices();
      const ukrainianVoice = voices.find(v => v.lang.startsWith('uk'));
      if (ukrainianVoice) {
        utterance.voice = ukrainianVoice;
      }
      
      if (this.onStateChange) {
        this.onStateChange({ isSpeaking: true });
      }
      
      utterance.onend = () => {
        if (this.onStateChange) {
          this.onStateChange({ isSpeaking: false });
        }
        resolve();
      };
      
      utterance.onerror = (event) => {
        if (this.onStateChange) {
          this.onStateChange({ isSpeaking: false });
        }
        reject(event);
      };
      
      speechSynthesis.speak(utterance);
    });
  }
  
  // Speak using Coqui TTS (Raspberry Pi)
  private async speakWithCoqui(text: string): Promise<void> {
    try {
      if (this.onStateChange) {
        this.onStateChange({ isSpeaking: true });
      }
      
      const response = await fetch(`${VOICE_API_URL}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language: 'uk' })
      });
      
      if (!response.ok) {
        throw new Error('TTS API error');
      }
      
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      return new Promise((resolve, reject) => {
        audio.onended = () => {
          URL.revokeObjectURL(audioUrl);
          if (this.onStateChange) {
            this.onStateChange({ isSpeaking: false });
          }
          resolve();
        };
        
        audio.onerror = (error) => {
          URL.revokeObjectURL(audioUrl);
          if (this.onStateChange) {
            this.onStateChange({ isSpeaking: false });
          }
          reject(error);
        };
        
        audio.play().catch(reject);
      });
      
    } catch (error) {
      console.error('[Voice] Coqui TTS error:', error);
      if (this.onStateChange) {
        this.onStateChange({ isSpeaking: false });
      }
      // Fallback to browser TTS
      return this.speak(text, false);
    }
  }
  
  // Process voice command
  parseCommand(text: string): { command: string; params?: any } | null {
    const lowerText = text.toLowerCase();
    
    // Water commands
    if (lowerText.includes('полий') || lowerText.includes('вода') || 
        lowerText.includes('water') || lowerText.includes('полити')) {
      return { command: 'water' };
    }
    
    // Light commands
    if (lowerText.includes('світло') || lowerText.includes('лампа') ||
        lowerText.includes('light') || lowerText.includes('увімкни')) {
      if (lowerText.includes('вимкни') || lowerText.includes('off')) {
        return { command: 'light_off' };
      }
      return { command: 'light_on' };
    }
    
    // Health check
    if (lowerText.includes('здоров') || lowerText.includes('стан') ||
        lowerText.includes('health') || lowerText.includes('how are you')) {
      return { command: 'health_check' };
    }
    
    // Sensor check
    if (lowerText.includes('сенсор') || lowerText.includes('дані') ||
        lowerText.includes('sensor') || lowerText.includes('data')) {
      return { command: 'show_sensors' };
    }
    
    // General chat
    return { command: 'chat', params: { message: text } };
  }
}

// Export singleton instance
export const voiceService = new VoiceService();

// Export helper hooks
export function useVoice() {
  return {
    isSupported: voiceService.isSupported(),
    startListening: () => voiceService.startListening(),
    stopListening: () => voiceService.stopListening(),
    speak: (text: string, useLocal?: boolean) => voiceService.speak(text, useLocal),
    parseCommand: (text: string) => voiceService.parseCommand(text),
    setCallbacks: voiceService.setCallbacks.bind(voiceService)
  };
}
