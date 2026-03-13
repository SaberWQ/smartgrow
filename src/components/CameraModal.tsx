import React, { useRef, useState, useEffect } from 'react';
import { X, Camera, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (base64: string) => void;
  title: string;
}

export default function CameraModal({ isOpen, onClose, onCapture, title }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
  }, [isOpen]);

  const startCamera = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      setStream(s);
      if (videoRef.current) {
        videoRef.current.srcObject = s;
      }
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Failed to access camera. Please check permissions.");
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  const capture = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const base64 = canvas.toDataURL('image/jpeg', 0.8);
        onCapture(base64);
      }
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-black/80 backdrop-blur-sm"
          />
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            className="relative w-full max-w-2xl bg-zinc-900 border-2 border-zinc-800 rounded-3xl overflow-hidden shadow-2xl"
          >
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/50">
              <div>
                <h3 className="text-xl font-bold font-display tracking-tight">Photo Verification</h3>
                <p className="text-sm text-zinc-400 font-mono">{title}</p>
              </div>
              <button onClick={onClose} className="p-2 hover:bg-zinc-800 rounded-full transition-colors">
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="relative aspect-video bg-black flex items-center justify-center">
              {error ? (
                <div className="p-8 text-center">
                  <p className="text-red-400 font-mono mb-4">{error}</p>
                  <button onClick={startCamera} className="flex items-center gap-2 mx-auto px-4 py-2 bg-zinc-800 rounded-lg hover:bg-zinc-700 transition-colors">
                    <RefreshCw className="w-4 h-4" /> Retry
                  </button>
                </div>
              ) : (
                <>
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 border-[40px] border-black/20 pointer-events-none">
                    <div className="w-full h-full border-2 border-green-500/50 border-dashed rounded-xl" />
                  </div>
                </>
              )}
            </div>

            <div className="p-8 flex justify-center bg-zinc-900">
              <button
                onClick={capture}
                disabled={!!error || !stream}
                className="group relative flex items-center justify-center w-20 h-20 bg-green-500 rounded-full shadow-lg shadow-green-500/20 hover:scale-105 active:scale-95 transition-all disabled:opacity-50 disabled:grayscale"
              >
                <Camera className="w-10 h-10 text-zinc-950" />
                <div className="absolute -inset-2 border-2 border-green-500/20 rounded-full animate-ping group-hover:animate-none" />
              </button>
            </div>
            <canvas ref={canvasRef} className="hidden" />
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
