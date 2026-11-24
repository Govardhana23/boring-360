import React from 'react';
import { 
  PlusCircle, Camera, Layers, Trash2, 
  Sparkles, ShieldCheck, Compass
} from 'lucide-react';
import { PanoramaMetadata } from '../types';

interface DashboardProps {
  panoramas: PanoramaMetadata[];
  onCreateNew: () => void;
  onSelectPanorama: (pano: PanoramaMetadata) => void;
  onDeletePanorama: (id: string, e: React.MouseEvent) => void;
  onLoadSample: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  panoramas,
  onCreateNew,
  onSelectPanorama,
  onDeletePanorama,
  onLoadSample,
}) => {
  const totalPanoramas = panoramas.length;
  const totalPhotosProcessed = panoramas.reduce((acc, p) => acc + p.input_image_count, 0);

  return (
    <div className="max-w-7xl mx-auto py-8 space-y-10">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-background border border-slate-800 p-8 sm:p-12 shadow-2xl">
        {/* Subtle background glow effect */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-20 w-80 h-80 rounded-full bg-teal-500/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-mono text-xs">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>AI-Assisted Smartphone Computer Vision</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
            Capture Reality. <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-400">
              Experience Everywhere.
            </span>
          </h1>

          <p className="text-base text-slate-300/90 leading-relaxed">
            Transform 8–12 regular smartphone photos into immersive, high-resolution panoramic experiences with authentic OpenCV feature matching, bundle adjustment, and interactive 360° navigation.
          </p>

          <div className="flex flex-wrap items-center gap-4 pt-4">
            <button
              onClick={onCreateNew}
              className="px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 text-slate-950 font-bold text-sm transition-all duration-300 shadow-glow-cyan flex items-center space-x-2"
            >
              <PlusCircle className="w-5 h-5" />
              <span>Create New Panorama</span>
            </button>

            <button
              onClick={onLoadSample}
              className="px-5 py-3.5 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-cyan-300 border border-cyan-500/30 font-semibold text-sm transition-all duration-300 flex items-center space-x-2"
            >
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>Try 1-Click Sample Dataset</span>
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Total Panoramas</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-white">
            {totalPanoramas}
          </p>
          <span className="text-xs text-slate-500 font-mono">
            {totalPanoramas === 0 ? 'Ready for your first project' : 'Stored in local SQLite'}
          </span>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Smartphone Photos Processed</span>
            <Camera className="w-4 h-4 text-teal-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-teal-400">
            {totalPhotosProcessed}
          </p>
          <span className="text-xs text-slate-500 font-mono">
            Keypoints extracted via SIFT / ORB
          </span>
        </div>

        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-mono uppercase tracking-wider">Stitching Engine</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-3xl font-extrabold font-mono text-emerald-400">
            OpenCV 5.1
          </p>
          <span className="text-xs text-slate-500 font-mono">
            PANORAMA & SCANS with Fallback
          </span>
        </div>
      </div>

      {/* Recent Projects Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Recent Panorama Projects
            </h2>
            <p className="text-xs text-slate-400">
              Interactive 360 experiences and stitched outputs
            </p>
          </div>

          {panoramas.length > 0 && (
            <button
              onClick={onCreateNew}
              className="text-xs text-cyan-400 hover:text-cyan-300 font-mono flex items-center space-x-1"
            >
              <span>+ New Project</span>
            </button>
          )}
        </div>

        {panoramas.length === 0 ? (
          /* Empty State */
          <div className="text-center py-16 px-4 rounded-3xl bg-slate-900/40 border border-dashed border-slate-800 space-y-4">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-slate-800/80 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <Camera className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-white">
              No panoramas generated yet
            </h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto">
              Get started by uploading 8–12 photos from your smartphone, or load our pre-configured sample room dataset with one click.
            </p>
            <div className="pt-2 flex justify-center gap-3">
              <button
                onClick={onCreateNew}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 text-slate-950 font-bold text-xs shadow-glow-cyan"
              >
                Create Panorama
              </button>
              <button
                onClick={onLoadSample}
                className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 font-medium text-xs"
              >
                Load Sample Dataset
              </button>
            </div>
          </div>
        ) : (
          /* Panorama Cards Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {panoramas.map((pano) => (
              <div
                key={pano.panorama_id}
                onClick={() => onSelectPanorama(pano)}
                className="group cursor-pointer rounded-2xl bg-slate-900 border border-slate-800 overflow-hidden hover:border-cyan-500/50 transition-all duration-300 hover:shadow-glow-cyan"
              >
                {/* Thumbnail Preview */}
                <div className="relative h-48 w-full bg-slate-950 overflow-hidden">
                  <img
                    src={pano.thumbnail_url || pano.image_url}
                    alt={pano.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />

                  {/* FOV Badge */}
                  <div className="absolute bottom-3 left-3 px-2 py-0.5 rounded-md bg-slate-900/90 backdrop-blur-sm border border-slate-700 text-[11px] font-mono font-medium text-cyan-300">
                    {pano.horizontal_fov}° FOV
                  </div>

                  {/* 360 icon indicator */}
                  <div className="absolute top-3 right-3 p-1.5 rounded-lg bg-slate-900/90 text-cyan-400 border border-slate-700">
                    <Compass className="w-4 h-4" />
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-4 space-y-2">
                  <div className="flex items-start justify-between">
                    <h3 className="font-bold text-white text-sm group-hover:text-cyan-300 transition-colors truncate">
                      {pano.title}
                    </h3>
                    <button
                      onClick={(e) => onDeletePanorama(pano.panorama_id, e)}
                      className="p-1 rounded text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-colors ml-2"
                      title="Delete panorama"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                    <span>{pano.width} x {pano.height} px</span>
                    <span>{pano.usable_image_count} photos</span>
                    <span>{pano.processing_time_seconds.toFixed(1)}s</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Start Capture Guide */}
      <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
          <Camera className="w-4 h-4 text-cyan-400" />
          <span>How To Capture Smartphone Panoramas</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs text-slate-300">
          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-1.5">
            <span className="font-mono text-cyan-400 font-bold">01. Single Viewpoint</span>
            <p className="text-slate-400 leading-relaxed">
              Stand in one spot. Rotate the smartphone in your hand around its optical axis rather than pacing around.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-1.5">
            <span className="font-mono text-cyan-400 font-bold">02. 30% Overlap</span>
            <p className="text-slate-400 leading-relaxed">
              Ensure each photo shares about a third of its frame with the previous shot so feature detectors find anchor points.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-1.5">
            <span className="font-mono text-cyan-400 font-bold">03. Consistent Height</span>
            <p className="text-slate-400 leading-relaxed">
              Keep the camera level at chest or eye height. Avoid tilting up and down between shots.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800/80 space-y-1.5">
            <span className="font-mono text-cyan-400 font-bold">04. Upload 8–12 Photos</span>
            <p className="text-slate-400 leading-relaxed">
              Upload the shots in sequence. Boring 360 handles orientation, alignment, seam blending and 360 viewer export.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
