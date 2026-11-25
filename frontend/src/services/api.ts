import { JobStatusResponse, PanoramaMetadata, PanoramaViewerConfig } from '../types';

const isLocal = typeof window !== 'undefined' && (
  window.location.hostname === 'localhost' || 
  window.location.hostname === '127.0.0.1'
);

export const BACKEND_ORIGIN = isLocal ? '' : 'https://boring360-backend.onrender.com';
export const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || `${BACKEND_ORIGIN}/api`;

export function resolveMediaUrl(url?: string | null): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  return `${BACKEND_ORIGIN}${url.startsWith('/') ? '' : '/'}${url}`;
}

export const api = {
  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE}/health`);
      return res.ok;
    } catch {
      return false;
    }
  },

  async createPanoramaJob(files: File[], title: string = 'Smartphone Panorama'): Promise<JobStatusResponse> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('title', title);

    const res = await fetch(`${API_BASE}/panoramas`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create panorama job' }));
      throw new Error(err.detail || 'Failed to upload images');
    }

    return res.json();
  },

  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch status for job ${jobId}`);
    }
    return res.json();
  },

  async getAllPanoramas(): Promise<PanoramaMetadata[]> {
    const res = await fetch(`${API_BASE}/panoramas`);
    if (!res.ok) {
      throw new Error('Failed to retrieve panoramas');
    }
    const data: PanoramaMetadata[] = await res.json();
    return data.map(item => ({
      ...item,
      image_url: resolveMediaUrl(item.image_url),
      thumbnail_url: item.thumbnail_url ? resolveMediaUrl(item.thumbnail_url) : undefined
    }));
  },

  async getPanorama(panoramaId: string): Promise<PanoramaMetadata> {
    const res = await fetch(`${API_BASE}/panoramas/${panoramaId}`);
    if (!res.ok) {
      throw new Error(`Failed to retrieve panorama ${panoramaId}`);
    }
    const data: PanoramaMetadata = await res.json();
    return {
      ...data,
      image_url: resolveMediaUrl(data.image_url),
      thumbnail_url: data.thumbnail_url ? resolveMediaUrl(data.thumbnail_url) : undefined
    };
  },

  async getPanoramaViewerConfig(panoramaId: string): Promise<PanoramaViewerConfig> {
    const res = await fetch(`${API_BASE}/panoramas/${panoramaId}/viewer`);
    if (!res.ok) {
      throw new Error(`Failed to retrieve viewer config for panorama ${panoramaId}`);
    }
    const data: PanoramaViewerConfig = await res.json();
    return {
      ...data,
      image_url: resolveMediaUrl(data.image_url)
    };
  },

  async deletePanorama(panoramaId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/panoramas/${panoramaId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      throw new Error(`Failed to delete panorama ${panoramaId}`);
    }
  },

  async getSampleDataset(): Promise<any> {
    const res = await fetch(`${API_BASE}/sample-dataset`);
    if (!res.ok) throw new Error('Failed to get sample dataset info');
    return res.json();
  },

  async createSamplePanorama(): Promise<JobStatusResponse> {
    const res = await fetch(`${API_BASE}/create-sample-panorama`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to create sample panorama');
    return res.json();
  },

  getImageUrl(panoramaId: string): string {
    return `${API_BASE}/panoramas/${panoramaId}/image`;
  }
};
