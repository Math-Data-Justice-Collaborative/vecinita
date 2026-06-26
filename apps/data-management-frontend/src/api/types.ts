export type JobStatus = "pending" | "running" | "completed" | "failed";
export type JobType = "ingest" | "retag";

export interface Job {
  job_id: string;
  status: JobStatus;
  job_type?: JobType;
  urls: string[];
  error_code?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobList {
  jobs: Job[];
}

export interface CreateJobResponse {
  job_id: string;
  status: JobStatus;
}

export interface DocumentSummary {
  document_id: string;
  url: string;
  title: string | null;
  language: string | null;
  tags?: TagInput[];
}

export interface TagInput {
  slug: string;
  label: string;
  source?: "llm" | "human";
}

export interface ChunkDetail {
  chunk_id: string;
  chunk_index: number;
  text: string;
  token_count: number | null;
  tags: TagInput[];
}
