export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface Segment {
  start: number;
  end: number;
  text: string;
}

export interface Transcription {
  text: string;
  language: string;
  model_name: string;
  segments: Segment[];
}

export interface Job {
  id: string;
  video_filename: string;
  language: string | null;
  model_name: string;
  status: JobStatus;
  created_at: string;
  completed_at: string | null;
  error: string | null;
  transcription?: Transcription | null;
}

export interface JobListItem {
  id: string;
  video_filename: string;
  language: string | null;
  model_name: string;
  status: JobStatus;
  created_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface JobCreateResponse {
  id: string;
  status: JobStatus;
  message: string;
}

export type WsEvent =
  | { event: "progress"; step: string; pct: number }
  | { event: "completed"; job: Job }
  | { event: "error"; message: string }
  | { event: "ping" };
