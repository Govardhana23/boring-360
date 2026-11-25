import React, { useState, useRef, useCallback } from 'react';
import { 
  Upload, X, ArrowLeft, ArrowRight, CheckCircle2, AlertTriangle, 
  Sparkles, Info, ShieldCheck, Compass, Camera
} from 'lucide-react';
import { UploadItem } from '../types';

interface UploadWorkflowProps {
  onStartProcessing: (files: File[], title: string) => void;
  onLoadSampleData: () => void;
  isLoadingSample: boolean;
}

export const UploadWorkflow: React.FC<UploadWorkflowProps> = ({ 
  onStartProcessing, 
  onLoadSampleData,
  isLoadingSample 
}) => {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [title, setTitle] = useState<string>('Smartphone Living Space Panorama');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFiles = useCallback((fileList: FileList | File[]) => {
    const newErrors: string[] = [];
    const validUploads: UploadItem[] = [];

    const allowedExtensions = ['.jpg', '.jpeg', '.png', '.webp'];

    Array.from(fileList).forEach((file) => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (!allowedExtensions.includes(ext)) {
        newErrors.push(`File "${file.name}" has unsupported format (${ext}). Allowed: JPG, PNG, WEBP.`);
        return;
      }

      if (file.size > 25 * 1024 * 1024) {
        newErrors.push(`File "${file.name}" exceeds 25MB limit (${(file.size / (1024 * 1024)).toFixed(1)}MB).`);
        return;
      }

      const previewUrl = URL.createObjectURL(file);
      const item: UploadItem = {
        id: Math.random().toString(36).substring(2, 9),
        file,
        previewUrl,
        name: file.name,
        size: file.size,
      };

      // Probe image dimensions
      const img = new Image();
      img.onload = () => {
        setItems(prev => prev.map(p => p.id === item.id ? { ...p, width: img.naturalWidth, height: img.naturalHeight } : p));
      };
      img.src = previewUrl;

      validUploads.push(item);
    });

    if (newErrors.length > 0) {
      setValidationErrors(newErrors);
    } else {
      setValidationErrors([]);
    }

    setItems((prev) => [...prev, ...validUploads]);
  }, []);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  };

  const removeItem = (id: string) => {
    setItems((prev) => {
      const target = prev.find(i => i.id === id);
      if (target) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((i) => i.id !== id);
    });
  };

  const moveItem = (index: number, direction: 'left' | 'right') => {
    const targetIndex = direction === 'left' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= items.length) return;

    setItems((prev) => {
      const next = [...prev];
      const temp = next[index];
      next[index] = next[targetIndex];
      next[targetIndex] = temp;
      return next;
    });
  };

  const handleClearAll = () => {
    items.forEach(i => URL.revokeObjectURL(i.previewUrl));
    setItems([]);
    setValidationErrors([]);
  };

  const handleGenerate = () => {
    if (items.length < 2) {
      setValidationErrors(['Please upload at least 2 overlapping photographs (8–12 recommended).']);
      return;
    }
    const files = items.map(i => i.file);
    onStartProcessing(files, title || 'Smartphone Panorama');
  };

  const isCountOptimal = items.length >= 8 && items.length <= 12;

  return (
    <div className="max-w-6xl mx-auto space-y-8 py-6">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-slate-800">
        <div className="space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-mono text-xs">
            <Camera className="w-3.5 h-3.5" />
            <span>OpenCV ORB Stitching Pipeline</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
            Turn Your Photos Into Immersive Panoramas.
          </h1>
          <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
            Upload 8–12 sequential overlapping smartphone photographs. Boring 360 detects ORB features, matches binary descriptors with Hamming distance, calculates RANSAC homographies, and blends them into an interactive panorama.
          </p>
        </div>

        {/* 1-Click Sample Dataset Button */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <button
            onClick={onLoadSampleData}
            disabled={isLoadingSample}
            className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700/80 text-cyan-300 border border-cyan-500/30 text-sm font-semibold transition-all shadow-sm hover:shadow-glow-cyan"
          >
            <Sparkles className={`w-4 h-4 text-cyan-400 ${isLoadingSample ? 'animate-spin' : ''}`} />
            <span>{isLoadingSample ? 'Loading Demo Set...' : 'Load Sample 8-Shot Dataset'}</span>
          </button>
        </div>
      </div>

      {/* Project Title Input */}
      <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 flex flex-col sm:flex-row items-center gap-4">
        <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider w-full sm:w-auto">
          Panorama Title:
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g., Living Room Sunset 360"
          className="w-full sm:flex-1 bg-slate-800/80 border border-slate-700 rounded-lg px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        />
        <div className="text-xs font-mono font-bold px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-cyan-400">
          Count: {items.length}/12
        </div>
      </div>

      {/* Upload Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-300 ${
          isDragging
            ? 'border-cyan-400 bg-cyan-950/20 shadow-glow-cyan scale-[1.005]'
            : 'border-slate-700 hover:border-slate-600 bg-slate-900/40 hover:bg-slate-900/60'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          multiple
          accept=".jpg,.jpeg,.png,.webp"
          className="hidden"
        />

        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-800 border border-cyan-500/20 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform">
          <Upload className="w-8 h-8" />
        </div>

        <h3 className="text-lg font-bold text-white mb-1">
          Drag and drop smartphone photos here
        </h3>
        <p className="text-sm text-slate-400 max-w-md mx-auto mb-4">
          Or <span className="text-cyan-400 underline font-medium">browse files</span> from your computer. Supported formats: JPG, JPEG, PNG, WEBP (up to 25MB each).
        </p>

        <div className="inline-flex items-center gap-3 px-4 py-2 rounded-lg bg-slate-800/80 border border-slate-700 text-xs text-slate-300 font-mono">
          <span className="text-cyan-400 font-bold">Image Counter:</span>
          <span className={`font-bold ${isCountOptimal ? 'text-teal-400' : 'text-amber-400'}`}>
            {items.length}/12 photographs selected
          </span>
          <span className="text-slate-500">•</span>
          <span>Recommended: 8–12 photos</span>
        </div>
      </div>

      {/* Validation Errors & Alerts */}
      {validationErrors.length > 0 && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-200 text-sm space-y-1">
          <div className="flex items-center gap-2 font-semibold text-red-300">
            <AlertTriangle className="w-4 h-4" />
            <span>Upload Notice:</span>
          </div>
          <ul className="list-disc list-inside space-y-0.5 text-xs text-red-300/90 pl-1">
            {validationErrors.map((err, idx) => (
              <li key={idx}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Thumbnails & Reordering Grid */}
      {items.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <h3 className="text-lg font-bold text-white">
                Selected Photographs ({items.length}/12)
              </h3>
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-mono font-medium ${
                isCountOptimal 
                  ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30'
                  : items.length < 8
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
              }`}>
                {items.length < 8 ? `${items.length}/12 (add ${8 - items.length} more for optimal 360)` : `${items.length}/12 (optimal)`}
              </span>
            </div>

            <button
              onClick={handleClearAll}
              className="text-xs text-slate-400 hover:text-red-400 transition-colors"
            >
              Clear all
            </button>
          </div>

          {/* Sequential Order Guidance note */}
          <div className="text-xs text-slate-400 flex items-center gap-2 bg-slate-900/40 p-2.5 rounded-lg border border-slate-800">
            <Info className="w-4 h-4 text-cyan-400 shrink-0" />
            <span>
              Arrange photos in rotational sequence order (Shot #1 $\rightarrow$ Shot #2 $\rightarrow$ ...). Use arrows to adjust ordering before stitching.
            </span>
          </div>

          {/* Grid of thumbnails */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3.5">
            {items.map((item, index) => (
              <div 
                key={item.id}
                className="group relative bg-slate-900 rounded-xl border border-slate-800 overflow-hidden hover:border-cyan-500/50 transition-all duration-200"
              >
                {/* Image Sequence Badge */}
                <div className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded-md bg-slate-950/80 backdrop-blur-sm text-[11px] font-mono font-bold text-cyan-300 border border-slate-700">
                  #{index + 1}
                </div>

                {/* Remove button */}
                <button
                  onClick={() => removeItem(item.id)}
                  className="absolute top-2 right-2 z-10 p-1 rounded-md bg-slate-950/80 hover:bg-red-500 text-slate-400 hover:text-white transition-colors"
                  title="Remove image"
                >
                  <X className="w-3.5 h-3.5" />
                </button>

                {/* Image Preview */}
                <div className="h-32 w-full bg-slate-950 flex items-center justify-center overflow-hidden">
                  <img
                    src={item.previewUrl}
                    alt={item.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </div>

                {/* Info & Reorder Controls */}
                <div className="p-2 bg-slate-900/90 text-[11px] space-y-1">
                  <p className="text-slate-200 font-medium truncate" title={item.name}>
                    {item.name}
                  </p>
                  <div className="flex items-center justify-between text-slate-400 font-mono text-[10px]">
                    <span>{(item.size / (1024 * 1024)).toFixed(1)}MB</span>
                    {item.width && item.height && (
                      <span>{item.width}x{item.height}</span>
                    )}
                  </div>

                  {/* Reorder Buttons */}
                  <div className="flex items-center justify-between pt-1 border-t border-slate-800/80">
                    <button
                      onClick={() => moveItem(index, 'left')}
                      disabled={index === 0}
                      className="p-1 rounded hover:bg-slate-800 disabled:opacity-20 text-slate-300"
                      title="Move left"
                    >
                      <ArrowLeft className="w-3 h-3" />
                    </button>
                    <span className="text-[10px] text-slate-500 font-mono">Pos {index + 1}</span>
                    <button
                      onClick={() => moveItem(index, 'right')}
                      disabled={index === items.length - 1}
                      className="p-1 rounded hover:bg-slate-800 disabled:opacity-20 text-slate-300"
                      title="Move right"
                    >
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Capture Guidelines Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-3">
          <div className="flex items-center space-x-2 text-cyan-400 font-bold text-sm">
            <ShieldCheck className="w-4 h-4" />
            <span>Smartphone Capture Guidelines</span>
          </div>
          <ul className="text-xs text-slate-300 space-y-2">
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              <span><strong>Same Position:</strong> Capture images from approximately the same physical location.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              <span><strong>25%–40% Overlap:</strong> Maintain consistent overlap between consecutive photos for feature matching.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              <span><strong>Rotate on Optical Center:</strong> Rotate the camera around its optical center to minimize parallax.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              <span><strong>Avoid Translation & Blur:</strong> Avoid sudden camera translation, motion blur, or drastic lighting changes.</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              <span><strong>Static Scene:</strong> Avoid moving people or objects in the overlapping boundary regions.</span>
            </li>
          </ul>
        </div>

        <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center space-x-2 text-slate-200 font-bold text-sm mb-2">
              <Compass className="w-4 h-4 text-cyan-400" />
              <span>Projection & Truth in Advertising</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              A sequence of 8–12 horizontally captured smartphone photos produces an authentic wide cylindrical panorama. The interactive viewer will truthfully display the actual angular coverage rather than falsely labelling a partial horizontal sweep as a complete 360° × 180° sphere.
            </p>
          </div>

          {/* Action CTA */}
          <div className="pt-2">
            <button
              onClick={handleGenerate}
              disabled={items.length < 2}
              className="w-full py-3.5 px-6 rounded-xl font-bold text-sm transition-all duration-300 flex items-center justify-center space-x-2 shadow-lg disabled:opacity-40 disabled:cursor-not-allowed bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 text-slate-950 shadow-glow-cyan"
            >
              <Sparkles className="w-4 h-4" />
              <span>GENERATE PANORAMA ({items.length}/12 SELECTED)</span>
            </button>
            {items.length < 2 && (
              <p className="text-[11px] text-slate-500 text-center mt-2 font-mono">
                Upload at least 2 images (8–12 recommended) to begin stitching
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
