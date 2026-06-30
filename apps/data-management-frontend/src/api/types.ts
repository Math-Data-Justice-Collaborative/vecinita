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

export type UserRole = "admin" | "viewer";
export type UserStatus = "active" | "invited" | "disabled";

export interface UserSummary {
  id: string;
  email: string;
  role: UserRole | null;
  status: UserStatus;
  created_at: string | null;
  last_sign_in_at: string | null;
}

export interface UserListResponse {
  users: UserSummary[];
  total: number | null;
  page: number;
  page_size: number;
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
