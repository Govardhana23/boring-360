import { JobStatusResponse, PanoramaMetadata, PanoramaViewerConfig } from '../types';

const API_BASE = '/api';

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
    return res.json();
  },

  async getPanorama(panoramaId: string): Promise<PanoramaMetadata> {
    const res = await fetch(`${API_BASE}/panoramas/${panoramaId}`);
    if (!res.ok) {
      throw new Error(`Failed to retrieve panorama ${panoramaId}`);
    }
    return res.json();
  },

  async getPanoramaViewerConfig(panoramaId: string): Promise<PanoramaViewerConfig> {
    const res = await fetch(`${API_BASE}/panoramas/${panoramaId}/viewer`);
    if (!res.ok) {
      throw new Error(`Failed to retrieve viewer config for panorama ${panoramaId}`);
    }
    return res.json();
  },

  async deletePanorama(panoramaId: string): Promise<void> {
    const res = await fetch(`${API_BASE}/panoramas/${panoramaId}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      throw new Error(`Failed to delete panorama ${panoramaId}`);
    }
  },

  getImageUrl(panoramaId: string): string {
    return `${API_BASE}/panoramas/${panoramaId}/image`;
  }
};
