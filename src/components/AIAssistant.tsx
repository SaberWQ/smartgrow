import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Bot, X, Sparkles, AlertTriangle, CheckCircle, Lightbulb, Send, Loader2 } from 'lucide-react';
import type { AIRecommendation, SensorData } from '../types';
import { getPlantCareAdvice } from '../services/gemini';

interface AIAssistantProps {
  recommendations: AIRecommendation[];
  sensors: SensorData;
  plantName: string;
  onDismiss: (id: string) => void;
  onAction: (action: string) => void;
}

const typeConfig = {
  warning: {
    icon: AlertTriangle,
    bg: 'from-amber-500/10 to-amber-500/5',
    border: 'border-amber-500/20',
    iconColor: 'text-amber-400',
    badge: 'bg-amber-500/20 text-amber-400'
  },
  suggestion: {
    icon: Lightbulb,
    bg: 'from-blue-500/10 to-blue-500/5',
    border: 'border-blue-500/20',
    iconColor: 'text-blue-400',
    badge: 'bg-blue-500/20 text-blue-400'
  },
  success: {
    icon: CheckCircle,
    bg: 'from-green-500/10 to-green-500/5',
    border: 'border-green-500/20',
    iconColor: 'text-green-400',
    badge: 'bg-green-500/20 text-green-400'
  }
};

export default function AIAssistant({ recommendations, sensors, plantName, onDismiss, onAction }: AIAssistantProps) {
  const [question, setQuestion] = useState('');
  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [isAsking, setIsAsking] = useState(false);

  const handleAskAI = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isAsking) return;

    setIsAsking(true);
    try {
      const response = await getPlantCareAdvice(question, plantName, sensors);
      setAiResponse(response);
      setQuestion('');
    } catch {
      setAiResponse("I'm having trouble connecting right now. Try again in a moment!");
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-br from-green-500/20 to-cyan-500/20 rounded-xl">
          <Bot className="w-5 h-5 text-green-400" />
        </div>
        <div>
          <h3 className="text-lg font-bold font-display">SmartGrow AI</h3>
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="font-mono">ONLINE</span>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="space-y-3 mb-6">
        <AnimatePresence mode="popLayout">
          {recommendations.map((rec) => {
            const config = typeConfig[rec.type];
            const Icon = config.icon;
            
            return (
              <motion.div
                key={rec.id}
                layout
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20, height: 0 }}
                className={`relative p-4 rounded-xl bg-gradient-to-br ${config.bg} border ${config.border}`}
              >
                <button
                  onClick={() => onDismiss(rec.id)}
                  className="absolute top-2 right-2 p-1 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4 text-zinc-500" />
                </button>
                
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${config.badge}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 pr-6">
                    <p className="text-sm leading-relaxed">{rec.message}</p>
                    {rec.action && (
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => onAction(rec.action!)}
                        className="mt-3 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-xs font-medium transition-colors"
                      >
                        {rec.action === 'water' && 'Water Now'}
                        {rec.action === 'light_on' && 'Turn On Light'}
                        {rec.action === 'light_off' && 'Turn Off Light'}
                        {rec.action === 'check_plant' && 'Check Plant'}
                      </motion.button>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {recommendations.length === 0 && !aiResponse && (
          <div className="text-center py-8 text-zinc-500">
            <Sparkles className="w-8 h-8 mx-auto mb-3 opacity-50" />
            <p className="text-sm">All systems optimal. Your plant is happy!</p>
          </div>
        )}
      </div>

      {/* AI Response */}
      <AnimatePresence>
        {aiResponse && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-4 p-4 bg-gradient-to-br from-green-500/10 to-cyan-500/10 border border-green-500/20 rounded-xl"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-500/20 rounded-lg">
                <Bot className="w-4 h-4 text-green-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm leading-relaxed">{aiResponse}</p>
                <button
                  onClick={() => setAiResponse(null)}
                  className="mt-2 text-xs text-zinc-500 hover:text-zinc-300"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Ask AI */}
      <form onSubmit={handleAskAI} className="relative">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask about your plant..."
          className="w-full px-4 py-3 pr-12 bg-zinc-900/50 border border-zinc-800 rounded-xl text-sm placeholder:text-zinc-600 focus:border-green-500/50 focus:outline-none transition-colors"
        />
        <button
          type="submit"
          disabled={!question.trim() || isAsking}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-green-500 hover:bg-green-600 disabled:bg-zinc-700 disabled:opacity-50 rounded-lg transition-colors"
        >
          {isAsking ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </form>
    </div>
  );
}
