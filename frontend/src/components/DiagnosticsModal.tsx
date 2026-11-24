import React from 'react';
import { X, ShieldCheck, AlertTriangle, CheckCircle2, Terminal, Info, BarChart2 } from 'lucide-react';
import { JobDiagnostics } from '../types';

interface DiagnosticsModalProps {
  diagnostics: JobDiagnostics | null;
  onClose: () => void;
}

export const DiagnosticsModal: React.FC<DiagnosticsModalProps> = ({ diagnostics, onClose }) => {
  if (!diagnostics) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="relative w-full max-w-4xl max-h-[85vh] bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center space-x-2.5">
            <BarChart2 className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-base font-bold text-white">
                Computer Vision Diagnostic Report
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                Method: {diagnostics.stitching_method_used} • Elapsed: {diagnostics.elapsed_time_seconds.toFixed(2)}s
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-300">
          {/* Per-Image Quality Assessment Table */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>Input Photographs Quality Assessment ({diagnostics.image_assessments.length})</span>
            </h4>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
              <table className="w-full text-left font-mono">
                <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-2.5">Image</th>
                    <th className="p-2.5">Resolution</th>
                    <th className="p-2.5">Laplacian Variance</th>
                    <th className="p-2.5">Brightness</th>
                    <th className="p-2.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {diagnostics.image_assessments.map((img, i) => (
                    <tr key={i} className="hover:bg-slate-900/40">
                      <td className="p-2.5 font-medium text-slate-200">{img.filename}</td>
                      <td className="p-2.5 text-slate-400">{img.width}x{img.height}</td>
                      <td className="p-2.5">
                        <span className={img.is_blurry ? 'text-amber-400 font-bold' : 'text-teal-400'}>
                          {img.laplacian_variance.toFixed(1)} {img.is_blurry ? '(Low Sharpness)' : '(Sharp)'}
                        </span>
                      </td>
                      <td className="p-2.5 text-slate-400">
                        {img.mean_brightness.toFixed(0)}/255
                        {img.is_underexposed && <span className="text-amber-400 ml-1">(Underexposed)</span>}
                        {img.is_overexposed && <span className="text-amber-400 ml-1">(Overexposed)</span>}
                      </td>
                      <td className="p-2.5">
                        {img.warnings.length === 0 ? (
                          <span className="text-teal-400 flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Optimal
                          </span>
                        ) : (
                          <span className="text-amber-400 flex items-center gap-1" title={img.warnings.join('; ')}>
                            <AlertTriangle className="w-3.5 h-3.5" /> {img.warnings.length} Notice
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pairwise Overlap Scores */}
          {diagnostics.pairwise_overlaps.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-300 flex items-center gap-2">
                <Info className="w-4 h-4 text-cyan-400" />
                <span>Pairwise Feature Overlap Analysis</span>
              </h4>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {diagnostics.pairwise_overlaps.map((pair, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 space-y-1 font-mono">
                    <div className="flex justify-between items-center text-slate-300">
                      <span className="truncate">{pair.image_a} &harr; {pair.image_b}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] ${
                        pair.sufficient_overlap 
                          ? 'bg-teal-500/10 text-teal-300 border border-teal-500/20' 
                          : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                      }`}>
                        {pair.good_matches} matches
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Estimated Overlap: ~{pair.estimated_overlap_percent}%
                    </div>
                    {pair.warning && (
                      <p className="text-[10px] text-amber-400/90 pt-1 border-t border-slate-800/80">
                        {pair.warning}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Raw OpenCV Logs */}
          {diagnostics.log_messages.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-cyan-400" />
                <span>Execution Log</span>
              </h4>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-400 max-h-40 overflow-y-auto space-y-1">
                {diagnostics.log_messages.map((log, idx) => (
                  <p key={idx}>{log}</p>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 flex justify-end bg-slate-900/90">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-colors"
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
};
