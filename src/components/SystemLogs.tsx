import { motion } from 'motion/react';
import { Terminal, Info, AlertTriangle, XCircle, CheckCircle } from 'lucide-react';
import type { SystemLog } from '../types';

interface SystemLogsProps {
  logs: SystemLog[];
}

const typeConfig = {
  info: {
    icon: Info,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10'
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10'
  },
  error: {
    icon: XCircle,
    color: 'text-red-400',
    bg: 'bg-red-500/10'
  },
  success: {
    icon: CheckCircle,
    color: 'text-green-400',
    bg: 'bg-green-500/10'
  }
};

export default function SystemLogs({ logs }: SystemLogsProps) {
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('uk-UA', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-zinc-800 rounded-xl">
          <Terminal className="w-5 h-5 text-green-400" />
        </div>
        <h3 className="text-lg font-bold font-display">System Logs</h3>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
        {logs.map((log, index) => {
          const config = typeConfig[log.type];
          const Icon = config.icon;

          return (
            <motion.div
              key={log.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center gap-3 p-3 bg-zinc-900/50 rounded-lg border border-zinc-800/50"
            >
              <div className={`p-1.5 rounded-lg ${config.bg}`}>
                <Icon className={`w-4 h-4 ${config.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm truncate">{log.message}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-zinc-600 font-mono">{formatTime(log.timestamp)}</span>
                  <span className="text-xs text-zinc-700">|</span>
                  <span className="text-xs text-zinc-500 uppercase">{log.source}</span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
