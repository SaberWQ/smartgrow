import { motion } from 'motion/react';
import { Heart, TrendingUp, Droplets, Calendar } from 'lucide-react';
import { GROWTH_STAGES, getGrowthStage } from '../services/mockData';
import type { PlantProfile } from '../types';

interface PlantStatusProps {
  plant: PlantProfile;
}

export default function PlantStatus({ plant }: PlantStatusProps) {
  const stage = getGrowthStage(plant.growthProgress);
  const stageInfo = GROWTH_STAGES[stage];
  const nextStage = Object.entries(GROWTH_STAGES).find(([_, info]) => info.min > plant.growthProgress);
  
  const progressInStage = ((plant.growthProgress - stageInfo.min) / (stageInfo.max - stageInfo.min)) * 100;
  
  const daysSincePlanted = Math.floor((Date.now() - new Date(plant.plantedAt).getTime()) / (1000 * 60 * 60 * 24));

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-green-500/10 rounded-xl">
          <span className="text-2xl">{stageInfo.icon}</span>
        </div>
        <div>
          <h3 className="text-lg font-bold font-display">{plant.name}</h3>
          <p className="text-sm text-zinc-500">{plant.species}</p>
        </div>
      </div>

      {/* Plant Avatar */}
      <div className="plant-avatar h-48 mb-6 flex items-center justify-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-center"
        >
          <motion.span 
            className="text-8xl block mb-2"
            animate={{ 
              scale: [1, 1.05, 1],
              rotate: [0, 2, -2, 0]
            }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            {stageInfo.icon}
          </motion.span>
          <span className="text-sm font-medium text-green-400">{stageInfo.name} Stage</span>
        </motion.div>
      </div>

      {/* Health Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Heart className={`w-4 h-4 ${plant.health >= 70 ? 'text-green-400' : plant.health >= 40 ? 'text-amber-400' : 'text-red-400'}`} />
            <span className="text-sm font-medium">Plant Health</span>
          </div>
          <span className="text-sm font-bold font-mono text-green-400">{plant.health}%</span>
        </div>
        <div className="progress-bar h-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${plant.health}%` }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className="h-full rounded-full"
            style={{
              background: plant.health >= 70 
                ? 'linear-gradient(90deg, #22c55e, #4ade80)'
                : plant.health >= 40
                ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                : 'linear-gradient(90deg, #ef4444, #f87171)'
            }}
          />
        </div>
      </div>

      {/* Growth Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <span className="text-sm font-medium">Growth Progress</span>
          </div>
          <span className="text-sm font-bold font-mono text-cyan-400">{plant.growthProgress}%</span>
        </div>
        <div className="progress-bar h-3">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${plant.growthProgress}%` }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className="h-full rounded-full"
            style={{ background: 'linear-gradient(90deg, #06b6d4, #22d3ee)' }}
          />
        </div>
        {nextStage && (
          <p className="text-xs text-zinc-500 mt-2">
            Next: {nextStage[1].icon} {nextStage[1].name} at {nextStage[1].min}%
          </p>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-1">
            <Droplets className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-zinc-500">Total Waterings</span>
          </div>
          <span className="text-xl font-bold font-mono">{plant.totalWaterings}</span>
        </div>
        <div className="stat-card">
          <div className="flex items-center gap-2 mb-1">
            <Calendar className="w-4 h-4 text-amber-400" />
            <span className="text-xs text-zinc-500">Days Growing</span>
          </div>
          <span className="text-xl font-bold font-mono">{daysSincePlanted}</span>
        </div>
      </div>
    </div>
  );
}
