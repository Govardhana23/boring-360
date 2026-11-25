import React from 'react';
import { 
  CheckCircle2, CircleDashed, AlertOctagon,
  RotateCcw, Cpu, Layers
} from 'lucide-react';
import { JobStatusResponse } from '../types';

interface ProcessingViewProps {
  status: JobStatusResponse | null;
  onRetry: () => void;
  onViewDiagnostics?: () => void;
}

const GENUINE_STAGES = [
  { 
    id: 1,
    key: 'validating', 
    label: '1. Validating photographs', 
    description: 'Verifying file formats, dimensions, and correcting smartphone EXIF orientation' 
  },
  { 
    id: 2,
    key: 'feature_detection', 
    label: '2. Extracting ORB features', 
    description: 'Detecting Oriented FAST keypoints and computing 256-bit Rotated BRIEF binary descriptors' 
  },
  { 
    id: 3,
    key: 'feature_matching', 
    label: '3. Matching image descriptors', 
    description: 'BFMatcher with Hamming distance & Lowe\'s ratio test filtering weak correspondences' 
  },
  { 
    id: 4,
    key: 'homography_ransac', 
    label: '4. Estimating homography with RANSAC', 
    description: 'Finding projective transformations between adjacent images and rejecting outliers' 
  },
  { 
    id: 5,
    key: 'aligning_blending', 
    label: '5. Aligning and blending images', 
    description: 'Warping onto common coordinate canvas, gain exposure compensation & distance feathering' 
  },
  { 
    id: 6,
    key: 'generating_panorama', 
    label: '6. Generating panorama', 
    description: 'Auto-cropping black margins, computing FOV metrics, and encoding high-resolution output' 
  },
];

export const ProcessingView: React.FC<ProcessingViewProps> = ({ 
  status, 
  onRetry,
  onViewDiagnostics
}) => {
  if (!status) return null;

  const currentStage = status.stage;
  const isFailed = currentStage === 'failed';
  const isCompleted = currentStage === 'completed';

  // Map backend progress percentage to genuine stage index (0 to 5)
  const getStageIndex = (stage: string, progress: number): number => {
    if (stage === 'completed' || progress >= 95) return 6;
    if (stage === 'failed') return -1;
    if (progress < 20) return 0; // Stage 1
    if (progress < 40) return 1; // Stage 2
    if (progress < 60) return 2; // Stage 3
    if (progress < 75) return 3; // Stage 4
    if (progress < 90) return 4; // Stage 5
    return 5; // Stage 6
  };

  const currentIndex = getStageIndex(currentStage, status.progress_percent);

  return (
    <div className="max-w-4xl mx-auto py-10 space-y-8">
      {/* Header status */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs">
          <Cpu className="w-3.5 h-3.5 animate-pulse" />
          <span>Genuine OpenCV ORB Pipeline In Execution</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
          {isFailed ? 'Panorama Stitching Failed' : isCompleted ? 'Panorama Stitched Successfully' : 'Synthesizing Panorama...'}
        </h2>
        <p className="text-sm text-slate-400 max-w-lg mx-auto">
          {status.message || 'Executing genuine computer vision operations across your photographs...'}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 space-y-3 shadow-xl">
        <div className="flex justify-between items-center text-xs font-mono">
          <span className="text-slate-400">Pipeline Execution Progress</span>
          <span className="text-cyan-400 font-bold">{status.progress_percent}%</span>
        </div>
        <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden">
          <div 
            className={`h-full transition-all duration-500 ${
              isFailed 
                ? 'bg-red-500' 
                : 'bg-gradient-to-r from-cyan-500 via-teal-400 to-emerald-400 shadow-glow-cyan'
            }`}
            style={{ width: `${Math.max(5, status.progress_percent)}%` }}
          />
        </div>
      </div>

      {/* Failure Box */}
      {isFailed && (
        <div className="p-6 rounded-2xl bg-red-950/40 border border-red-500/40 space-y-4">
          <div className="flex items-start gap-3">
            <AlertOctagon className="w-6 h-6 text-red-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-base font-bold text-red-200">
                Stitching Error Encountered
              </h3>
              <p className="text-sm text-red-300/90 mt-1">
                {status.error || 'OpenCV could not find sufficient matching features or camera alignment between the input photographs.'}
              </p>
              <p className="text-xs text-red-400/80 mt-2">
                Tip: Ensure 25%–40% overlap between consecutive photographs, avoid moving subjects in the seams, and rotate around the phone's camera axis.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={onRetry}
              className="px-4 py-2 rounded-xl bg-red-900/60 hover:bg-red-800/80 text-white text-xs font-bold transition-colors flex items-center space-x-1.5 border border-red-500/50"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retry With Adjusted Photos</span>
            </button>
            {onViewDiagnostics && (
              <button
                onClick={onViewDiagnostics}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
              >
                Inspect Logs
              </button>
            )}
          </div>
        </div>
      )}

      {/* 6 Genuine Processing Stages Checklist */}
      <div className="bg-slate-900/50 rounded-2xl border border-slate-800 p-6 space-y-4 shadow-xl">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center space-x-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span>Core Computer Vision Stages</span>
        </h3>

        <div className="space-y-3">
          {GENUINE_STAGES.map((stg, idx) => {
            const isDone = isCompleted || currentIndex > idx;
            const isCurrent = !isFailed && !isCompleted && currentIndex === idx;

            return (
              <div 
                key={stg.id}
                className={`flex items-start space-x-3.5 p-3.5 rounded-xl border transition-all duration-300 ${
                  isDone 
                    ? 'bg-slate-900/60 border-teal-500/20 text-slate-300' 
                    : isCurrent 
                    ? 'bg-cyan-950/30 border-cyan-500/40 text-white shadow-glow-cyan' 
                    : 'bg-slate-950/40 border-slate-800/60 text-slate-500'
                }`}
              >
                <div className="shrink-0 mt-0.5">
                  {isDone ? (
                    <CheckCircle2 className="w-5 h-5 text-teal-400" />
                  ) : isCurrent ? (
                    <CircleDashed className="w-5 h-5 text-cyan-400 animate-spin" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border border-slate-700 flex items-center justify-center text-[10px] font-mono text-slate-600">
                      {stg.id}
                    </div>
                  )}
                </div>

                <div className="flex-1 space-y-0.5">
                  <div className="flex items-center justify-between">
                    <p className={`text-sm font-semibold ${isDone ? 'text-teal-300' : isCurrent ? 'text-cyan-300' : 'text-slate-400'}`}>
                      {stg.label}
                    </p>
                    {isCurrent && (
                      <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded-md bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 animate-pulse">
                        RUNNING
                      </span>
                    )}
                    {isDone && (
                      <span className="text-[10px] font-mono font-medium text-teal-400">
                        VERIFIED
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {stg.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
