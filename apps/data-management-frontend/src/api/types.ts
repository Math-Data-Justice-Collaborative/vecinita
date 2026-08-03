export type JobStatus =
  "pending" | "running" | "completed" | "failed" | "cancelled";
export type JobType = "ingest" | "retag" | "eval" | "rebuild";
export type RebuildMode = "reembed" | "rechunk" | "rescrape";
export type BackfillSource = "rescrape" | "from_chunks";

export interface Job {
  job_id: string;
  status: JobStatus;
  job_type?: JobType | undefined;
  urls: string[];
  document_id?: string | null | undefined;
  eval_run_id?: string | null | undefined;
  modal_call_id?: string | null | undefined;
  dashboard_url?: string | null | undefined;
  error_code?: string | null | undefined;
  error_message?: string | null | undefined;
  created_at: string;
  updated_at: string;
}

export interface CreateJobOptions {
  chunk_size_tokens?: number;
  job_type?: JobType;
  mode?: RebuildMode;
  force?: boolean;
  dry_run?: boolean;
  document_ids?: string[];
  backfill?: boolean;
  backfill_source?: BackfillSource;
  ack_reconstruct_from_chunks?: boolean;
  crawl?: boolean;
  max_depth?: number;
  max_pages?: number;
  crawl_scope?: "same_domain" | "path_prefix";
}

export interface CreateJobResponse {
  job_id: string;
  status: JobStatus;
}

export interface JobList {
  jobs: Job[];
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
