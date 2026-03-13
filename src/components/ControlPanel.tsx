import { motion } from 'motion/react';
import { Droplets, Sun, Zap, Settings, Power } from 'lucide-react';
import type { GreenhouseControls } from '../types';

interface ControlPanelProps {
  controls: GreenhouseControls;
  onTogglePump: () => void;
  onToggleUV: () => void;
  onToggleAutoWatering: () => void;
  onToggleAutoLighting: () => void;
  isWatering?: boolean;
}

export default function ControlPanel({
  controls,
  onTogglePump,
  onToggleUV,
  onToggleAutoWatering,
  onToggleAutoLighting,
  isWatering = false
}: ControlPanelProps) {
  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-green-500/10 rounded-xl">
          <Settings className="w-5 h-5 text-green-400" />
        </div>
        <h3 className="text-lg font-bold font-display">Control Center</h3>
      </div>

      <div className="space-y-4">
        {/* Manual Controls */}
        <div className="space-y-3">
          <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Manual Controls</span>
          
          <div className="grid grid-cols-2 gap-3">
            {/* Water Pump */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onTogglePump}
              className={`relative p-4 rounded-2xl border transition-all ${
                controls.pumpActive
                  ? 'bg-gradient-to-br from-cyan-500/20 to-cyan-500/5 border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                  : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'
              }`}
            >
              <div className="flex flex-col items-center gap-2">
                <div className={`p-3 rounded-xl ${controls.pumpActive ? 'bg-cyan-500/20' : 'bg-zinc-800'}`}>
                  <Droplets className={`w-6 h-6 ${controls.pumpActive ? 'text-cyan-400 water-wave' : 'text-zinc-500'}`} />
                </div>
                <span className="text-sm font-medium">{isWatering ? 'Watering...' : 'Water Pump'}</span>
                <span className={`text-xs font-mono ${controls.pumpActive ? 'text-cyan-400' : 'text-zinc-500'}`}>
                  {controls.pumpActive ? 'ACTIVE' : 'OFF'}
                </span>
              </div>
              {controls.pumpActive && (
                <motion.div
                  className="absolute inset-0 rounded-2xl border-2 border-cyan-400/50"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}
            </motion.button>

            {/* UV Light */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onToggleUV}
              className={`relative p-4 rounded-2xl border transition-all ${
                controls.uvLightActive
                  ? 'bg-gradient-to-br from-amber-500/20 to-amber-500/5 border-amber-500/30 shadow-lg shadow-amber-500/10'
                  : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'
              }`}
            >
              <div className="flex flex-col items-center gap-2">
                <div className={`p-3 rounded-xl ${controls.uvLightActive ? 'bg-amber-500/20' : 'bg-zinc-800'}`}>
                  <Sun className={`w-6 h-6 ${controls.uvLightActive ? 'text-amber-400 animate-pulse' : 'text-zinc-500'}`} />
                </div>
                <span className="text-sm font-medium">UV Light</span>
                <span className={`text-xs font-mono ${controls.uvLightActive ? 'text-amber-400' : 'text-zinc-500'}`}>
                  {controls.uvLightActive ? 'ON' : 'OFF'}
                </span>
              </div>
              {controls.uvLightActive && (
                <motion.div
                  className="absolute inset-0 rounded-2xl"
                  style={{ background: 'radial-gradient(circle at center, rgba(245, 158, 11, 0.1) 0%, transparent 70%)' }}
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                />
              )}
            </motion.button>
          </div>
        </div>

        {/* Automation Controls */}
        <div className="space-y-3 pt-4 border-t border-zinc-800">
          <span className="text-xs font-mono text-zinc-500 uppercase tracking-wider">Automation</span>
          
          {/* Auto Watering Toggle */}
          <div className="flex items-center justify-between p-4 bg-zinc-900/50 rounded-xl border border-zinc-800">
            <div className="flex items-center gap-3">
              <Zap className={`w-5 h-5 ${controls.autoWateringEnabled ? 'text-green-400' : 'text-zinc-500'}`} />
              <div>
                <span className="text-sm font-medium">Auto Watering</span>
                <p className="text-xs text-zinc-500">Waters when moisture {'<'} {controls.wateringThreshold}%</p>
              </div>
            </div>
            <button
              onClick={onToggleAutoWatering}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                controls.autoWateringEnabled ? 'bg-green-500' : 'bg-zinc-700'
              }`}
            >
              <motion.div
                className="absolute top-1 w-4 h-4 rounded-full bg-white shadow-md"
                animate={{ left: controls.autoWateringEnabled ? '26px' : '4px' }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            </button>
          </div>

          {/* Auto Lighting Toggle */}
          <div className="flex items-center justify-between p-4 bg-zinc-900/50 rounded-xl border border-zinc-800">
            <div className="flex items-center gap-3">
              <Power className={`w-5 h-5 ${controls.autoLightingEnabled ? 'text-amber-400' : 'text-zinc-500'}`} />
              <div>
                <span className="text-sm font-medium">Auto Lighting</span>
                <p className="text-xs text-zinc-500">
                  {controls.lightingSchedule.startHour}:00 - {controls.lightingSchedule.endHour}:00
                </p>
              </div>
            </div>
            <button
              onClick={onToggleAutoLighting}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                controls.autoLightingEnabled ? 'bg-amber-500' : 'bg-zinc-700'
              }`}
            >
              <motion.div
                className="absolute top-1 w-4 h-4 rounded-full bg-white shadow-md"
                animate={{ left: controls.autoLightingEnabled ? '26px' : '4px' }}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
