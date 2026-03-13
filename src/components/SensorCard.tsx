import { motion } from 'motion/react';
import type { ReactNode } from 'react';

interface SensorCardProps {
  title: string;
  value: string | number;
  unit: string;
  icon: ReactNode;
  color: 'green' | 'cyan' | 'amber' | 'blue';
  percentage?: number;
  status?: 'optimal' | 'warning' | 'critical';
  trend?: 'up' | 'down' | 'stable';
}

const colorClasses = {
  green: {
    bg: 'from-green-500/10 to-green-500/5',
    border: 'border-green-500/20',
    text: 'text-green-400',
    glow: 'shadow-green-500/10'
  },
  cyan: {
    bg: 'from-cyan-500/10 to-cyan-500/5',
    border: 'border-cyan-500/20',
    text: 'text-cyan-400',
    glow: 'shadow-cyan-500/10'
  },
  amber: {
    bg: 'from-amber-500/10 to-amber-500/5',
    border: 'border-amber-500/20',
    text: 'text-amber-400',
    glow: 'shadow-amber-500/10'
  },
  blue: {
    bg: 'from-blue-500/10 to-blue-500/5',
    border: 'border-blue-500/20',
    text: 'text-blue-400',
    glow: 'shadow-blue-500/10'
  }
};

const statusColors = {
  optimal: 'bg-green-500',
  warning: 'bg-amber-500',
  critical: 'bg-red-500'
};

export default function SensorCard({
  title,
  value,
  unit,
  icon,
  color,
  percentage,
  status = 'optimal',
  trend
}: SensorCardProps) {
  const classes = colorClasses[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -2 }}
      className={`sensor-card bg-gradient-to-br ${classes.bg} border ${classes.border} hover:shadow-lg ${classes.glow} transition-shadow`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl bg-gradient-to-br ${classes.bg} ${classes.text}`}>
            {icon}
          </div>
          <span className="text-sm font-medium text-zinc-400">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          {trend && (
            <span className={`text-xs ${trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-zinc-500'}`}>
              {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
            </span>
          )}
          <div className={`w-2 h-2 rounded-full ${statusColors[status]} pulse-dot`} />
        </div>
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-1 mb-4">
        <span className={`text-4xl font-bold font-mono ${classes.text}`}>
          {value}
        </span>
        <span className="text-lg text-zinc-500">{unit}</span>
      </div>

      {/* Progress bar */}
      {percentage !== undefined && (
        <div className="space-y-2">
          <div className="progress-bar">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(percentage, 100)}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="progress-bar-fill"
              style={{
                background: status === 'critical' 
                  ? 'linear-gradient(90deg, #ef4444, #f87171)'
                  : status === 'warning'
                  ? 'linear-gradient(90deg, #f59e0b, #fbbf24)'
                  : `linear-gradient(90deg, ${color === 'green' ? '#22c55e, #4ade80' : color === 'cyan' ? '#06b6d4, #22d3ee' : color === 'amber' ? '#f59e0b, #fbbf24' : '#3b82f6, #60a5fa'})`
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-zinc-500 font-mono">
            <span>0%</span>
            <span>{percentage}%</span>
            <span>100%</span>
          </div>
        </div>
      )}
    </motion.div>
  );
}
