export type JobStatus =
  "pending" | "running" | "completed" | "failed" | "cancelled";
export type JobType = "ingest" | "retag" | "eval" | "rebuild";
export type RebuildMode = "reembed" | "rechunk" | "rescrape";
export type BackfillSource = "rescrape" | "from_chunks";

export interface JobUrlFailure {
  url: string;
  error_code: string;
  error_message: string;
}

export interface JobMetrics {
  skipped_unchanged?: number;
  urls_failed_embed?: number;
  urls_failed_scrape?: number;
  url_failures?: JobUrlFailure[];
  pages_fetched?: number;
  pages_failed?: number;
  pages_skipped_robots?: number;
  crawl_stopped_reason?: string | null;
  translated_documents?: number;
  translated_chunks?: number;
  translation_skipped?: number;
  translation_failed?: number;
}

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
  metrics?: JobMetrics | null | undefined;
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
  translate_locales?: Array<"en" | "es">;

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
  display_title?: string | null;
  language: string | null;
  tags?: TagInput[];
  source_domain?: string | null;
  source_path?: string | null;
  parent_url?: string | null;
  canonical_url?: string | null;
}

export interface DocumentMetadataPatch {
  display_title?: string | null;
  title?: string | null;
  language?: string | null;
}

export interface DocumentMetadataResponse {
  document_id: string;
  url: string;
  title: string | null;
  display_title: string | null;
  language: string | null;
}

export type TreeNodeKind = "domain" | "path" | "document" | "chunk";

export interface TreeNode {
  id: string;
  kind: TreeNodeKind;
  label: string;
  url?: string | null;
  status?: string | null;
  counts?: Record<string, number> | null;
  source_domain?: string | null;
  source_path?: string | null;
  parent_url?: string | null;
  canonical_url?: string | null;
  children?: TreeNode[];
}

export interface CorpusTreeResponse {
  roots: TreeNode[];
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
