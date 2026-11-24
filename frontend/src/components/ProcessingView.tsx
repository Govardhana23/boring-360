import React from 'react';
import { 
  CheckCircle2, CircleDashed, AlertOctagon, Terminal, 
  RotateCcw, Cpu
} from 'lucide-react';
import { JobStatusResponse, JobStage } from '../types';

interface ProcessingViewProps {
  status: JobStatusResponse | null;
  onRetry: () => void;
  onViewDiagnostics?: () => void;
}

const STAGES: { key: JobStage; label: string; description: string }[] = [
  { key: 'validating', label: '1. Upload Validation', description: 'Checking file formats, dimensions, and file integrity' },
  { key: 'preprocessing', label: '2. Image Preprocessing', description: 'Correcting smartphone EXIF rotation & scaling resolution' },
  { key: 'feature_detection', label: '3. Feature Detection', description: 'Extracting scale-invariant keypoints (SIFT / ORB)' },
  { key: 'feature_matching', label: '4. Feature Matching', description: 'Matching keypoints with Lowe\'s ratio test & FLANN' },
  { key: 'camera_alignment', label: '5. Camera Alignment', description: 'Estimating camera poses via RANSAC homography & bundle adjustment' },
  { key: 'image_warping', label: '6. Image Warping', description: 'Projecting photos onto cylindrical coordinate space' },
  { key: 'seam_blending', label: '7. Seam Blending', description: 'Multi-band blending, exposure compensation & border cropping' },
  { key: 'generating_panorama', label: '8. Panorama Generation', description: 'Encoding high-resolution panorama and computing FOV metrics' },
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

  const getStageIndex = (stage: JobStage): number => {
    switch (stage) {
      case 'queued': return -1;
      case 'validating': return 0;
      case 'preprocessing': return 1;
      case 'feature_detection': return 2;
      case 'feature_matching': return 3;
      case 'camera_alignment': return 4;
      case 'image_warping': return 5;
      case 'seam_blending': return 6;
      case 'generating_panorama': return 7;
      case 'completed': return 8;
      case 'failed': return 99;
      default: return 0;
    }
  };

  const currentIndex = getStageIndex(currentStage);

  return (
    <div className="max-w-4xl mx-auto py-10 space-y-8">
      {/* Header status */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-mono text-xs">
          <Cpu className="w-3.5 h-3.5 animate-pulse" />
          <span>Active Computer Vision Engine</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
          {isFailed ? 'Panorama Generation Failed' : isCompleted ? 'Panorama Stitched Successfully' : 'Synthesizing Panorama...'}
        </h2>
        <p className="text-sm text-slate-400 max-w-lg mx-auto">
          {status.message || 'Processing overlapping smartphone photographs via OpenCV...'}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 space-y-3 shadow-xl">
        <div className="flex justify-between items-center text-xs font-mono">
          <span className="text-slate-400">Progress</span>
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
            </div>
          </div>

          <div className="p-4 bg-slate-950/70 rounded-xl border border-red-900/40 text-xs font-mono text-slate-300 space-y-1">
            <p className="text-red-400 font-semibold">// Diagnostic troubleshooting:</p>
            <p>1. Check that consecutive photos share at least 30% visual overlap.</p>
            <p>2. Avoid scenes with blank featureless walls or moving subjects.</p>
            <p>3. Ensure photos are uploaded in left-to-right sequential order.</p>
          </div>

          <div className="flex items-center space-x-3 pt-2">
            <button
              onClick={onRetry}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold flex items-center space-x-2 border border-slate-700 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Try With Different Photos</span>
            </button>
            {onViewDiagnostics && (
              <button
                onClick={onViewDiagnostics}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-bold flex items-center space-x-2 border border-slate-700 transition-colors"
              >
                <span>View Error Diagnostics</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Stages Stepper */}
      <div className="bg-slate-900/60 rounded-2xl border border-slate-800 p-6 space-y-4">
        <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider font-mono">
          Pipeline Processing Stages
        </h3>

        <div className="space-y-3">
          {STAGES.map((s, idx) => {
            const isDone = currentIndex > idx;
            const isCurrent = currentIndex === idx && !isFailed;
            const isError = isFailed && currentIndex === idx;

            return (
              <div 
                key={s.key}
                className={`p-3.5 rounded-xl border transition-all duration-300 flex items-center justify-between ${
                  isCurrent 
                    ? 'bg-cyan-950/30 border-cyan-500/50 shadow-glow-cyan'
                    : isDone
                    ? 'bg-slate-900/80 border-slate-800 opacity-90'
                    : isError
                    ? 'bg-red-950/30 border-red-500/50'
                    : 'bg-slate-900/30 border-slate-800/50 opacity-40'
                }`}
              >
                <div className="flex items-center space-x-3">
                  {isDone ? (
                    <CheckCircle2 className="w-5 h-5 text-teal-400 shrink-0" />
                  ) : isCurrent ? (
                    <CircleDashed className="w-5 h-5 text-cyan-400 animate-spin shrink-0" />
                  ) : isError ? (
                    <AlertOctagon className="w-5 h-5 text-red-400 shrink-0" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border border-slate-700 flex items-center justify-center text-[10px] text-slate-500 font-mono">
                      {idx + 1}
                    </div>
                  )}
                  <div>
                    <h4 className={`text-sm font-semibold ${isCurrent ? 'text-cyan-300' : isDone ? 'text-slate-200' : 'text-slate-400'}`}>
                      {s.label}
                    </h4>
                    <p className="text-xs text-slate-500">
                      {s.description}
                    </p>
                  </div>
                </div>

                {isCurrent && (
                  <span className="text-xs font-mono text-cyan-400 px-2 py-0.5 rounded-md bg-cyan-500/10 border border-cyan-500/20 animate-pulse">
                    Processing
                  </span>
                )}
                {isDone && (
                  <span className="text-xs font-mono text-teal-400">
                    Done
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Real-time Diagnostics Logs */}
      {status.diagnostics?.log_messages && status.diagnostics.log_messages.length > 0 && (
        <div className="bg-slate-950 rounded-2xl border border-slate-800 p-5 space-y-3 font-mono">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 text-slate-300 font-semibold">
              <Terminal className="w-3.5 h-3.5 text-cyan-400" />
              <span>Backend OpenCV Diagnostic Stream</span>
            </span>
            <span className="text-[10px] text-slate-500">
              {status.diagnostics.log_messages.length} log lines
            </span>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-1 text-xs text-slate-300 p-3 bg-slate-900/60 rounded-xl border border-slate-800/80">
            {status.diagnostics.log_messages.map((log, idx) => (
              <p key={idx} className="leading-relaxed">
                <span className="text-cyan-500 mr-2">&gt;</span>
                {log}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
