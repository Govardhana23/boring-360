export type JobStage =
  | 'queued'
  | 'validating'
  | 'preprocessing'
  | 'feature_detection'
  | 'feature_matching'
  | 'camera_alignment'
  | 'image_warping'
  | 'seam_blending'
  | 'generating_panorama'
  | 'completed'
  | 'failed';

export interface ImageQualityAssessment {
  filename: string;
  width: number;
  height: number;
  file_size_bytes: number;
  laplacian_variance: number;
  is_blurry: boolean;
  mean_brightness: number;
  is_underexposed: boolean;
  is_overexposed: boolean;
  underexposed_percent: number;
  overexposed_percent: number;
  warnings: string[];
  recommendations: string[];
}

export interface PairwiseOverlapScore {
  image_a: string;
  image_b: string;
  keypoints_a: number;
  keypoints_b: number;
  good_matches: number;
  estimated_overlap_percent: number;
  sufficient_overlap: boolean;
  warning?: string;
}

export interface JobDiagnostics {
  input_image_count: number;
  usable_image_count: number;
  image_assessments: ImageQualityAssessment[];
  pairwise_overlaps: PairwiseOverlapScore[];
  stitching_method_used: string;
  stitching_status_code: number;
  stitching_status_message: string;
  is_full_360: boolean;
  horizontal_fov_degrees: number;
  vertical_fov_degrees: number;
  output_width: number;
  output_height: number;
  aspect_ratio: number;
  elapsed_time_seconds: number;
  warnings: string[];
  log_messages: string[];
}

export interface JobStatusResponse {
  job_id: string;
  panorama_id?: string;
  stage: JobStage;
  progress_percent: number;
  message: string;
  error?: string;
  created_at: string;
  updated_at: string;
  diagnostics?: JobDiagnostics;
}

export interface PanoramaMetadata {
  panorama_id: string;
  job_id: string;
  title: string;
  filename: string;
  image_url: string;
  thumbnail_url?: string;
  width: number;
  height: number;
  aspect_ratio: number;
  file_size_bytes: number;
  input_image_count: number;
  usable_image_count: number;
  processing_time_seconds: number;
  is_full_360: boolean;
  horizontal_fov: number;
  vertical_fov: number;
  stitching_method: string;
  created_at: string;
  diagnostics?: JobDiagnostics;
}

export interface PanoramaViewerConfig {
  panorama_id: string;
  image_url: string;
  type: string;
  is_full_360: boolean;
  haov: number;
  vaov: number;
  v_offset: number;
  auto_rotate: number;
  compass: boolean;
  hfov: number;
  min_hfov: number;
  max_hfov: number;
  title: string;
  description: string;
}

export interface UploadItem {
  id: string;
  file: File;
  previewUrl: string;
  name: string;
  size: number;
  width?: number;
  height?: number;
}
