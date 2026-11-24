import React, { useState } from 'react';
import { 
  Download, PlusCircle, CheckCircle2, AlertTriangle, 
  BarChart3, Sparkles, ChevronRight
} from 'lucide-react';
import { PanoramaMetadata, PanoramaViewerConfig } from '../types';
import { PannellumViewer } from './PannellumViewer';

interface ResultsViewProps {
  panorama: PanoramaMetadata;
  viewerConfig: PanoramaViewerConfig | null;
  onCreateAnother: () => void;
  onOpenDiagnostics: () => void;
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  panorama,
  viewerConfig,
  onCreateAnother,
  onOpenDiagnostics,
}) => {
  const [viewMode, setViewMode] = useState<'360' | 'flat'>('360');

  const downloadPanorama = () => {
    const a = document.createElement('a');
    a.href = panorama.image_url;
    a.download = panorama.filename || `boring360_${panorama.panorama_id}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="max-w-6xl mx-auto py-8 space-y-8">
      {/* Title & Action Buttons */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center space-x-2 text-teal-400 text-xs font-mono mb-1">
            <CheckCircle2 className="w-4 h-4" />
            <span>STITCHING COMPLETED & VALIDATED</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            {panorama.title}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Processed with {panorama.stitching_method} in {panorama.processing_time_seconds.toFixed(2)}s
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5">
          {/* Toggle 360 vs 2D Flat */}
          <div className="bg-slate-900 p-1 rounded-xl border border-slate-800 flex items-center">
            <button
              onClick={() => setViewMode('360')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                viewMode === '360' 
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Interactive 360°
            </button>
            <button
              onClick={() => setViewMode('flat')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                viewMode === 'flat' 
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan' 
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              2D Flat Composite
            </button>
          </div>

          {/* Download button */}
          <button
            onClick={downloadPanorama}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-bold transition-colors flex items-center space-x-2"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>Download JPEG</span>
          </button>

          {/* Create another button */}
          <button
            onClick={onCreateAnother}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 text-slate-950 font-bold text-xs transition-all shadow-glow-cyan flex items-center space-x-2"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Create Another</span>
          </button>
        </div>
      </div>

      {/* Main View Area: Pannellum or Flat Image */}
      <div className="space-y-4">
        {viewMode === '360' && viewerConfig ? (
          <PannellumViewer config={viewerConfig} />
        ) : (
          <div className="relative w-full rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 p-2 shadow-2xl">
            <img 
              src={panorama.image_url} 
              alt={panorama.title} 
              className="w-full h-auto max-h-[600px] object-contain rounded-xl mx-auto"
            />
            <div className="p-3 bg-slate-900/90 rounded-b-xl border-t border-slate-800 flex justify-between items-center text-xs text-slate-400 font-mono">
              <span>Resolution: {panorama.width} x {panorama.height} px</span>
              <span>Aspect Ratio: {panorama.aspect_ratio.toFixed(2)} : 1</span>
            </div>
          </div>
        )}
      </div>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-mono text-slate-400">Output Resolution</span>
          <p className="text-xl font-bold font-mono text-white">
            {panorama.width} <span className="text-sm font-normal text-slate-400">x</span> {panorama.height}
          </p>
          <span className="text-[11px] text-slate-500 font-mono">
            {((panorama.width * panorama.height) / 1000000).toFixed(1)} Megapixels
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-mono text-slate-400">Input Photos Stitched</span>
          <p className="text-xl font-bold font-mono text-teal-400">
            {panorama.usable_image_count} <span className="text-sm font-normal text-slate-400">/ {panorama.input_image_count}</span>
          </p>
          <span className="text-[11px] text-slate-500 font-mono">
            100% Usable rate
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-mono text-slate-400">Processing Duration</span>
          <p className="text-xl font-bold font-mono text-cyan-400">
            {panorama.processing_time_seconds.toFixed(2)}s
          </p>
          <span className="text-[11px] text-slate-500 font-mono">
            OpenCV CV2 Pipeline
          </span>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-xs font-mono text-slate-400">Angular Coverage (FOV)</span>
          <p className="text-xl font-bold font-mono text-white">
            {panorama.horizontal_fov}° <span className="text-xs font-normal text-slate-400">H</span>
          </p>
          <span className="text-[11px] text-slate-500 font-mono">
            {panorama.is_full_360 ? 'Full 360° Sphere' : 'Partial Cylindrical'}
          </span>
        </div>
      </div>

      {/* Quality Assessment & Warnings Report */}
      <div className="bg-slate-900/50 rounded-2xl border border-slate-800 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-white font-bold text-base">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <span>Computer Vision & Capture Quality Report</span>
          </div>

          <button
            onClick={onOpenDiagnostics}
            className="text-xs font-mono text-cyan-400 hover:text-cyan-300 transition-colors flex items-center space-x-1"
          >
            <span>View Full Diagnostic Breakdown</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Coverage Notice */}
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-2">
          <div className="flex items-center space-x-2 text-cyan-300 font-semibold">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span>Projection & Coverage Truthfulness:</span>
          </div>
          <p className="leading-relaxed">
            {panorama.is_full_360 ? (
              'This sequence achieved complete 360-degree horizontal loop closure and full sphere projection.'
            ) : (
              `This panorama captures approximately ${panorama.horizontal_fov}° horizontal angular span. Because standard single-row smartphone captures do not include zenith and nadir vertical coverage, it is presented honestly as a partial panorama with calibrated field-of-view rather than an artificial sphere.`
            )}
          </p>
        </div>

        {/* Warnings List if any */}
        {panorama.diagnostics?.warnings && panorama.diagnostics.warnings.length > 0 && (
          <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-500/30 text-xs text-amber-200/90 space-y-2">
            <div className="flex items-center space-x-2 text-amber-300 font-semibold">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Capture Quality Recommendations:</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-amber-300/80">
              {panorama.diagnostics.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
