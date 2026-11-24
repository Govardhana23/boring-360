import React from 'react';
import { Layers, PlusCircle } from 'lucide-react';

interface NavbarProps {
  activeTab: 'dashboard' | 'create' | 'gallery';
  setActiveTab: (tab: 'dashboard' | 'create' | 'gallery') => void;
  isBackendHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, isBackendHealthy }) => {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-background/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div 
          onClick={() => setActiveTab('dashboard')} 
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="relative w-10 h-10 flex items-center justify-center rounded-xl bg-slate-900 border border-cyan-500/30 group-hover:border-cyan-400 transition-all duration-300 shadow-glow-cyan">
            {/* SVG Logo */}
            <svg className="w-6 h-6 text-cyan-400 transition-transform duration-500 group-hover:rotate-90" viewBox="0 0 100 100" fill="none">
              <circle cx="50" cy="50" r="42" stroke="currentColor" strokeWidth="6" strokeDasharray="14 10" opacity="0.7"/>
              <circle cx="50" cy="50" r="28" stroke="#14b8a6" strokeWidth="5"/>
              <circle cx="50" cy="50" r="14" fill="#06b6d4"/>
              <circle cx="53" cy="47" r="4" fill="#ffffff" opacity="0.9"/>
            </svg>
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-extrabold text-lg tracking-wider text-white">BORING</span>
              <span className="font-mono text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-teal-400">360</span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium tracking-wider uppercase hidden sm:block">
              Capture Reality. Experience Everywhere.
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 sm:space-x-2">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${
              activeTab === 'dashboard'
                ? 'bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => setActiveTab('create')}
            className={`px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 flex items-center space-x-2 ${
              activeTab === 'create'
                ? 'bg-gradient-to-r from-cyan-500/20 to-teal-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow-cyan'
                : 'text-slate-300 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60'
            }`}
          >
            <PlusCircle className="w-4 h-4 text-cyan-400" />
            <span>New Panorama</span>
          </button>
        </nav>

        {/* Backend Status indicator */}
        <div className="flex items-center space-x-2.5 pl-3 border-l border-slate-800 text-xs">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-900 border border-slate-800">
            <span className={`w-2 h-2 rounded-full ${isBackendHealthy ? 'bg-teal-400 animate-pulse' : 'bg-red-400'}`} />
            <span className="text-slate-300 font-mono text-[11px] hidden md:inline">
              {isBackendHealthy ? 'OpenCV Core Ready' : 'Backend Connecting...'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
