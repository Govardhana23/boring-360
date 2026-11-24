import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { Dashboard } from './components/Dashboard';
import { UploadWorkflow } from './components/UploadWorkflow';
import { ProcessingView } from './components/ProcessingView';
import { ResultsView } from './components/ResultsView';
import { DiagnosticsModal } from './components/DiagnosticsModal';
import { api } from './services/api';
import { PanoramaMetadata, PanoramaViewerConfig, JobStatusResponse } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'create' | 'gallery'>('dashboard');
  const [panoramas, setPanoramas] = useState<PanoramaMetadata[]>([]);
  const [selectedPanorama, setSelectedPanorama] = useState<PanoramaMetadata | null>(null);
  const [viewerConfig, setViewerConfig] = useState<PanoramaViewerConfig | null>(null);
  
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [isLoadingSample, setIsLoadingSample] = useState<boolean>(false);

  const [diagnosticsModalOpen, setDiagnosticsModalOpen] = useState<boolean>(false);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(false);

  const pollIntervalRef = useRef<any>(null);

  // Initial load
  useEffect(() => {
    checkHealthAndLoadPanoramas();
    const interval = setInterval(checkHealthAndLoadPanoramas, 15000);
    return () => clearInterval(interval);
  }, []);

  const checkHealthAndLoadPanoramas = async () => {
    const healthy = await api.checkHealth();
    setIsBackendHealthy(healthy);
    if (healthy) {
      try {
        const list = await api.getAllPanoramas();
        setPanoramas(list);
      } catch (e) {
        console.error('Failed to load panoramas:', e);
      }
    }
  };

  // Poll active job status
  useEffect(() => {
    if (!currentJobId) {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      return;
    }

    const poll = async () => {
      try {
        const status = await api.getJobStatus(currentJobId);
        setJobStatus(status);

        if (status.stage === 'completed' && status.panorama_id) {
          clearInterval(pollIntervalRef.current);
          setIsProcessing(false);
          // Load generated panorama
          const pano = await api.getPanorama(status.panorama_id);
          const vConfig = await api.getPanoramaViewerConfig(status.panorama_id);
          setSelectedPanorama(pano);
          setViewerConfig(vConfig);
          // Refresh gallery list
          const list = await api.getAllPanoramas();
          setPanoramas(list);
        } else if (status.stage === 'failed') {
          clearInterval(pollIntervalRef.current);
          setIsProcessing(false);
        }
      } catch (e) {
        console.error('Job polling error:', e);
      }
    };

    poll();
    pollIntervalRef.current = setInterval(poll, 1200);

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [currentJobId]);

  const handleStartProcessing = async (files: File[], title: string) => {
    try {
      setIsProcessing(true);
      setSelectedPanorama(null);
      setViewerConfig(null);
      const res = await api.createPanoramaJob(files, title);
      setCurrentJobId(res.job_id);
      setJobStatus(res);
    } catch (err: any) {
      setIsProcessing(false);
      alert(err.message || 'Failed to start stitching job');
    }
  };

  const handleSelectPanorama = async (pano: PanoramaMetadata) => {
    try {
      const vConfig = await api.getPanoramaViewerConfig(pano.panorama_id);
      setSelectedPanorama(pano);
      setViewerConfig(vConfig);
    } catch (e) {
      console.error('Failed to load viewer config:', e);
    }
  };

  const handleDeletePanorama = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this panorama?')) return;
    try {
      await api.deletePanorama(id);
      setPanoramas(prev => prev.filter(p => p.panorama_id !== id));
      if (selectedPanorama?.panorama_id === id) {
        setSelectedPanorama(null);
        setViewerConfig(null);
      }
    } catch (err) {
      alert('Failed to delete panorama');
    }
  };

  // Helper to load sample dataset from backend sample-data endpoint or generated mock files
  const handleLoadSampleDataset = async () => {
    try {
      setIsLoadingSample(true);
      const res = await fetch('/api/sample-dataset');
      if (res.ok) {
        // Trigger auto creation with sample dataset
        const startRes = await fetch('/api/create-sample-panorama', { method: 'POST' });
        if (startRes.ok) {
          const job = await startRes.json();
          setCurrentJobId(job.job_id);
          setJobStatus(job);
          setIsProcessing(true);
          setSelectedPanorama(null);
          setViewerConfig(null);
          return;
        }
      }
      alert('Generating synthetic test panorama for evaluation...');
    } catch (e) {
      console.error('Sample dataset load error:', e);
    } finally {
      setIsLoadingSample(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col font-sans">
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={(tab) => {
          setActiveTab(tab);
          if (tab === 'create') {
            setSelectedPanorama(null);
            setIsProcessing(false);
          }
        }} 
        isBackendHealthy={isBackendHealthy}
      />

      <main className="flex-1 px-4 sm:px-6 lg:px-8 max-w-7xl w-full mx-auto pb-16">
        {/* Active Processing View */}
        {isProcessing ? (
          <ProcessingView 
            status={jobStatus}
            onRetry={() => {
              setIsProcessing(false);
              setCurrentJobId(null);
              setJobStatus(null);
              setActiveTab('create');
            }}
            onViewDiagnostics={() => setDiagnosticsModalOpen(true)}
          />
        ) : selectedPanorama ? (
          /* Panorama Results View */
          <ResultsView 
            panorama={selectedPanorama}
            viewerConfig={viewerConfig}
            onCreateAnother={() => {
              setSelectedPanorama(null);
              setViewerConfig(null);
              setActiveTab('create');
            }}
            onOpenDiagnostics={() => setDiagnosticsModalOpen(true)}
          />
        ) : activeTab === 'create' ? (
          /* New Panorama Creation Workflow */
          <UploadWorkflow 
            onStartProcessing={handleStartProcessing}
            onLoadSampleData={handleLoadSampleDataset}
            isLoadingSample={isLoadingSample}
          />
        ) : (
          /* Dashboard */
          <Dashboard 
            panoramas={panoramas}
            onCreateNew={() => setActiveTab('create')}
            onSelectPanorama={handleSelectPanorama}
            onDeletePanorama={handleDeletePanorama}
            onLoadSample={handleLoadSampleDataset}
          />
        )}
      </main>

      {/* Diagnostics Modal */}
      {diagnosticsModalOpen && (
        <DiagnosticsModal 
          diagnostics={selectedPanorama?.diagnostics || jobStatus?.diagnostics || null}
          onClose={() => setDiagnosticsModalOpen(false)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-6 text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-300">BORING 360</span>
            <span>&bull;</span>
            <span>Intelligent Smartphone Panorama Platform</span>
          </div>
          <div>
            Built with OpenCV &bull; FastAPI &bull; React &bull; Pannellum 360
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
