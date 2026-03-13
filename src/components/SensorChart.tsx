import { useMemo } from 'react';
import { motion } from 'motion/react';
import { Activity } from 'lucide-react';
import type { SensorData } from '../types';

interface SensorChartProps {
  data: SensorData[];
  dataKey: keyof SensorData;
  title: string;
  color: string;
  unit: string;
}

export default function SensorChart({ data, dataKey, title, color, unit }: SensorChartProps) {
  const { points, min, max, current } = useMemo(() => {
    if (!data.length) return { points: '', min: 0, max: 100, current: 0 };
    
    const values = data.map(d => d[dataKey] as number);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal || 1;
    const padding = range * 0.1;
    
    const normalizedMin = minVal - padding;
    const normalizedMax = maxVal + padding;
    const normalizedRange = normalizedMax - normalizedMin;
    
    const width = 300;
    const height = 80;
    
    const pathPoints = data.map((d, i) => {
      const x = (i / (data.length - 1)) * width;
      const y = height - ((d[dataKey] as number - normalizedMin) / normalizedRange) * height;
      return `${x},${y}`;
    }).join(' ');
    
    return {
      points: pathPoints,
      min: Math.round(minVal),
      max: Math.round(maxVal),
      current: Math.round(values[values.length - 1])
    };
  }, [data, dataKey]);

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('uk-UA', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl" style={{ backgroundColor: `${color}20` }}>
            <Activity className="w-5 h-5" style={{ color }} />
          </div>
          <span className="text-sm font-medium text-zinc-400">{title}</span>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold font-mono" style={{ color }}>{current}</span>
          <span className="text-sm text-zinc-500 ml-1">{unit}</span>
        </div>
      </div>

      <div className="relative h-20 mb-2">
        <svg
          viewBox="0 0 300 80"
          className="w-full h-full"
          preserveAspectRatio="none"
        >
          {/* Grid lines */}
          <line x1="0" y1="20" x2="300" y2="20" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
          <line x1="0" y1="40" x2="300" y2="40" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
          <line x1="0" y1="60" x2="300" y2="60" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
          
          {/* Area fill */}
          <defs>
            <linearGradient id={`gradient-${dataKey}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={color} stopOpacity="0" />
            </linearGradient>
          </defs>
          
          {points && (
            <>
              {/* Area */}
              <motion.polygon
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1 }}
                points={`0,80 ${points} 300,80`}
                fill={`url(#gradient-${dataKey})`}
              />
              
              {/* Line */}
              <motion.polyline
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 1.5, ease: "easeOut" }}
                points={points}
                fill="none"
                stroke={color}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              
              {/* Current value dot */}
              <motion.circle
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 1, duration: 0.3 }}
                cx="300"
                cy={points.split(' ').pop()?.split(',')[1]}
                r="4"
                fill={color}
              />
            </>
          )}
        </svg>
      </div>

      <div className="flex items-center justify-between text-xs text-zinc-600 font-mono">
        <span>{data.length > 0 ? formatTime(data[0].timestamp) : '--:--'}</span>
        <span className="flex items-center gap-4">
          <span>Min: {min}{unit}</span>
          <span>Max: {max}{unit}</span>
        </span>
        <span>{data.length > 0 ? formatTime(data[data.length - 1].timestamp) : '--:--'}</span>
      </div>
    </div>
  );
}
