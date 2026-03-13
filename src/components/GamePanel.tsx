import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Trophy, 
  Coins, 
  Flame, 
  Target, 
  CheckCircle, 
  Sparkles,
  ChevronRight,
  Lock,
  Star
} from 'lucide-react';
import type { UserProfile, Achievement, DailyTask } from '../types';
import { calculateLevelFromXp, ALL_ACHIEVEMENTS } from '../services/mockData';

interface GamePanelProps {
  profile: UserProfile;
  achievements: Achievement[];
  dailyTasks: DailyTask[];
  onCompleteTask: (taskId: string) => void;
}

export default function GamePanel({ profile, achievements, dailyTasks, onCompleteTask }: GamePanelProps) {
  const [activeTab, setActiveTab] = useState<'tasks' | 'achievements'>('tasks');
  const levelInfo = calculateLevelFromXp(profile.xp);
  const xpProgress = (levelInfo.currentLevelXp / levelInfo.nextLevelXp) * 100;

  const unlockedAchievementIds = achievements.filter(a => a.unlockedAt).map(a => a.id);
  const completedTasksCount = dailyTasks.filter(t => t.completed).length;

  return (
    <div className="glass-card p-6">
      {/* Header Stats */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-amber-500/20 to-orange-500/20 rounded-xl">
            <Trophy className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold font-display">Game Progress</h3>
            <div className="flex items-center gap-2 text-xs">
              <Flame className="w-3 h-3 text-orange-400" />
              <span className="text-orange-400 font-mono">{profile.streak} day streak</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 border border-amber-500/20 rounded-xl">
          <Coins className="w-4 h-4 text-amber-400" />
          <span className="font-bold font-mono text-amber-400">{profile.gold}</span>
        </div>
      </div>

      {/* Level Progress */}
      <div className="mb-6 p-4 bg-zinc-900/50 rounded-xl border border-zinc-800">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-cyan-500 flex items-center justify-center font-bold font-mono text-lg">
              {levelInfo.level}
            </div>
            <div>
              <span className="text-sm font-medium">Level {levelInfo.level}</span>
              <p className="text-xs text-zinc-500">Plant Guardian</p>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs text-zinc-500">XP</span>
            <p className="text-sm font-mono font-bold text-green-400">
              {levelInfo.currentLevelXp} / {levelInfo.nextLevelXp}
            </p>
          </div>
        </div>
        <div className="progress-bar h-2">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${xpProgress}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="h-full rounded-full"
            style={{ background: 'linear-gradient(90deg, #22c55e, #06b6d4)' }}
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab('tasks')}
          className={`flex-1 py-2 px-4 rounded-xl font-medium text-sm transition-all ${
            activeTab === 'tasks'
              ? 'bg-green-500 text-zinc-900'
              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
          }`}
        >
          <span className="flex items-center justify-center gap-2">
            <Target className="w-4 h-4" />
            Tasks ({completedTasksCount}/{dailyTasks.length})
          </span>
        </button>
        <button
          onClick={() => setActiveTab('achievements')}
          className={`flex-1 py-2 px-4 rounded-xl font-medium text-sm transition-all ${
            activeTab === 'achievements'
              ? 'bg-amber-500 text-zinc-900'
              : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
          }`}
        >
          <span className="flex items-center justify-center gap-2">
            <Star className="w-4 h-4" />
            Badges ({unlockedAchievementIds.length}/{ALL_ACHIEVEMENTS.length})
          </span>
        </button>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'tasks' ? (
          <motion.div
            key="tasks"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className="space-y-3"
          >
            {dailyTasks.map((task) => (
              <motion.div
                key={task.id}
                layout
                className={`p-4 rounded-xl border transition-all ${
                  task.completed
                    ? 'bg-green-500/10 border-green-500/20'
                    : 'bg-zinc-900/50 border-zinc-800 hover:border-zinc-700'
                }`}
              >
                <div className="flex items-start gap-3">
                  <button
                    onClick={() => !task.completed && onCompleteTask(task.id)}
                    disabled={task.completed}
                    className={`mt-0.5 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors ${
                      task.completed
                        ? 'bg-green-500 border-green-500'
                        : 'border-zinc-600 hover:border-green-500'
                    }`}
                  >
                    {task.completed && <CheckCircle className="w-4 h-4 text-zinc-900" />}
                  </button>
                  <div className="flex-1">
                    <span className={`text-sm font-medium ${task.completed ? 'line-through text-zinc-500' : ''}`}>
                      {task.title}
                    </span>
                    <p className="text-xs text-zinc-500 mt-1">{task.description}</p>
                    <div className="flex items-center gap-4 mt-2">
                      <span className="flex items-center gap-1 text-xs text-cyan-400">
                        <Sparkles className="w-3 h-3" /> +{task.rewardXp} XP
                      </span>
                      <span className="flex items-center gap-1 text-xs text-amber-400">
                        <Coins className="w-3 h-3" /> +{task.rewardGold}
                      </span>
                    </div>
                  </div>
                  {!task.completed && (
                    <ChevronRight className="w-5 h-5 text-zinc-600" />
                  )}
                </div>
              </motion.div>
            ))}

            {dailyTasks.length === 0 && (
              <div className="text-center py-8 text-zinc-500">
                <Target className="w-8 h-8 mx-auto mb-3 opacity-50" />
                <p className="text-sm">No tasks available. Check back later!</p>
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div
            key="achievements"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="grid grid-cols-3 gap-3"
          >
            {ALL_ACHIEVEMENTS.map((achievement) => {
              const isUnlocked = unlockedAchievementIds.includes(achievement.id);
              
              return (
                <motion.div
                  key={achievement.id}
                  whileHover={{ scale: 1.05 }}
                  className={`achievement-badge ${isUnlocked ? 'unlocked' : 'locked'} text-center p-3`}
                >
                  <span className="text-3xl block mb-2">
                    {isUnlocked ? achievement.icon : <Lock className="w-8 h-8 mx-auto text-zinc-600" />}
                  </span>
                  <span className={`text-xs font-medium ${isUnlocked ? 'text-zinc-200' : 'text-zinc-600'}`}>
                    {achievement.name}
                  </span>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
