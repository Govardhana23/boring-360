import React, { useEffect, useRef, useState } from 'react';
import { 
  Maximize2, Minimize2, RotateCw, ZoomIn, ZoomOut, 
  RotateCcw, Info, X
} from 'lucide-react';
import { PanoramaViewerConfig } from '../types';

interface PannellumViewerProps {
  config: PanoramaViewerConfig;
  onClose?: () => void;
}

declare global {
  interface Window {
    pannellum: any;
  }
}

export const PannellumViewer: React.FC<PannellumViewerProps> = ({ config, onClose }) => {
  const viewerContainerRef = useRef<HTMLDivElement>(null);
  const viewerInstanceRef = useRef<any>(null);
  const [isAutoRotating, setIsAutoRotating] = useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  useEffect(() => {
    const containerId = `pannellum-viewer-${config.panorama_id}`;
    if (!viewerContainerRef.current) return;

    // Wait until Pannellum script is loaded on window
    const checkAndInit = () => {
      if (window.pannellum) {
        // Destroy existing instance if any
        if (viewerInstanceRef.current) {
          try {
            viewerInstanceRef.current.destroy();
          } catch (e) {
            // ignore
          }
        }

        try {
          const viewerOptions: any = {
            type: 'equirectangular',
            panorama: config.image_url,
            autoLoad: true,
            autoRotate: isAutoRotating ? (config.auto_rotate || -1.5) : 0,
            compass: true,
            showZoomCtrl: false,
            showFullscreenCtrl: false,
            haov: config.haov || 360,
            vaov: config.vaov || 180,
            vOffset: config.v_offset || 0,
            hfov: config.hfov || 100,
            minHfov: config.min_hfov || 35,
            maxHfov: config.max_hfov || 120,
            backgroundColor: [9, 13, 22],
            crossOrigin: 'anonymous',
          };

          const viewer = window.pannellum.viewer(containerId, viewerOptions);
          viewerInstanceRef.current = viewer;
        } catch (err) {
          console.error('Failed to initialize Pannellum:', err);
        }
      } else {
        setTimeout(checkAndInit, 100);
      }
    };

    checkAndInit();

    return () => {
      if (viewerInstanceRef.current) {
        try {
          viewerInstanceRef.current.destroy();
        } catch (e) {}
      }
    };
  }, [config, config.panorama_id]);

  const toggleAutoRotate = () => {
    if (!viewerInstanceRef.current) return;
    if (isAutoRotating) {
      viewerInstanceRef.current.stopAutoRotate();
      setIsAutoRotating(false);
    } else {
      viewerInstanceRef.current.startAutoRotate(config.auto_rotate || -1.5);
      setIsAutoRotating(true);
    }
  };

  const handleZoomIn = () => {
    if (viewerInstanceRef.current) {
      const cur = viewerInstanceRef.current.getHfov();
      viewerInstanceRef.current.setHfov(Math.max(config.min_hfov || 35, cur - 10));
    }
  };

  const handleZoomOut = () => {
    if (viewerInstanceRef.current) {
      const cur = viewerInstanceRef.current.getHfov();
      viewerInstanceRef.current.setHfov(Math.min(config.max_hfov || 120, cur + 10));
    }
  };

  const handleResetView = () => {
    if (viewerInstanceRef.current) {
      viewerInstanceRef.current.setPitch(0);
      viewerInstanceRef.current.setYaw(0);
      viewerInstanceRef.current.setHfov(config.hfov || 100);
    }
  };

  const toggleFullscreen = () => {
    if (!viewerContainerRef.current) return;
    if (!document.fullscreenElement) {
      viewerContainerRef.current.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  return (
    <div className="relative w-full h-[650px] bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl group">
      {/* Pannellum DOM mount container */}
      <div 
        ref={viewerContainerRef}
        id={`pannellum-viewer-${config.panorama_id}`}
        className="w-full h-full"
      />

      {/* Top Banner & Projection Mode Badge */}
      <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between pointer-events-none">
        <div className="flex items-center space-x-2.5 pointer-events-auto">
          <div className="px-3 py-1.5 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-700/80 text-xs font-mono text-white shadow-lg flex items-center space-x-2">
            <span className={`w-2 h-2 rounded-full ${config.is_full_360 ? 'bg-teal-400' : 'bg-cyan-400'} animate-pulse`} />
            <span className="font-semibold">{config.title}</span>
          </div>

          {/* Partial vs Full Sphere Badge */}
          <div className={`px-2.5 py-1 rounded-xl backdrop-blur-md text-xs font-mono border flex items-center space-x-1.5 shadow-lg ${
            config.is_full_360 
              ? 'bg-teal-950/80 border-teal-500/40 text-teal-300'
              : 'bg-cyan-950/80 border-cyan-500/40 text-cyan-300'
          }`}>
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>
              {config.is_full_360 
                ? '360° × 180° Full Sphere' 
                : `Partial Panorama (${config.haov}° H × ${config.vaov}° V)`}
            </span>
          </div>
        </div>

        {/* Close Button if rendered as modal */}
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-slate-900/90 hover:bg-red-500 text-slate-300 hover:text-white transition-colors border border-slate-700 pointer-events-auto shadow-lg"
            title="Close viewer"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Floating Control Toolbar */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center space-x-2 px-3 py-2 rounded-2xl bg-slate-900/90 backdrop-blur-md border border-slate-700/80 shadow-2xl">
        {/* Auto Rotate Toggle */}
        <button
          onClick={toggleAutoRotate}
          className={`p-2 rounded-xl text-xs font-medium transition-colors flex items-center space-x-1.5 ${
            isAutoRotating 
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' 
              : 'hover:bg-slate-800 text-slate-300'
          }`}
          title={isAutoRotating ? 'Pause rotation' : 'Start smooth auto-rotation'}
        >
          <RotateCw className={`w-4 h-4 ${isAutoRotating ? 'animate-spin' : ''}`} style={{ animationDuration: '6s' }} />
          <span className="hidden sm:inline text-xs">Auto-rotate</span>
        </button>

        <div className="w-[1px] h-5 bg-slate-700 mx-1" />

        {/* Zoom In */}
        <button
          onClick={handleZoomIn}
          className="p-2 rounded-xl hover:bg-slate-800 text-slate-300 transition-colors"
          title="Zoom in"
        >
          <ZoomIn className="w-4 h-4" />
        </button>

        {/* Zoom Out */}
        <button
          onClick={handleZoomOut}
          className="p-2 rounded-xl hover:bg-slate-800 text-slate-300 transition-colors"
          title="Zoom out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>

        {/* Reset View */}
        <button
          onClick={handleResetView}
          className="p-2 rounded-xl hover:bg-slate-800 text-slate-300 transition-colors"
          title="Reset viewpoint"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        <div className="w-[1px] h-5 bg-slate-700 mx-1" />

        {/* Fullscreen Toggle */}
        <button
          onClick={toggleFullscreen}
          className="p-2 rounded-xl hover:bg-slate-800 text-slate-300 transition-colors"
          title="Toggle fullscreen"
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* Projection Notice at bottom right */}
      {!config.is_full_360 && (
        <div className="absolute bottom-4 right-4 z-10 hidden md:block max-w-xs p-2.5 rounded-xl bg-slate-950/80 backdrop-blur-md border border-slate-800 text-[11px] text-slate-400">
          <p className="font-semibold text-cyan-400 mb-0.5">True Geometry Notice</p>
          Single-row smartphone rotation produces cylindrical angular span ({config.haov}°). Viewing bounds are constrained to prevent artificial spherical distortion.
        </div>
      )}
    </div>
  );
};
