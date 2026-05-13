/**
 * Hand-written **FR-010** DTOs for corpus/dashboard HTTP JSON (not covered by the scraper OpenAPI snapshot).
 * Scraper job types live in `dm-openapi.generated.ts` / `modal-types.ts`.
 */

export interface Document {
  id: string;
  title: string;
  description: string;
  url: string;
  resource_type: 'website' | 'document' | 'organization' | 'dataset' | 'service';
  format: 'HTML' | 'PDF' | 'API' | 'video' | 'TXT' | 'DOCX' | 'other';
  language: string;
  organization: string;
  content?: string;
  embedding_status?: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  tags?: string[];
  scrape_depth?: number;
}

export interface ScrapeRequest {
  url: string;
  depth: number;
  auto_tag?: boolean;
  user_id?: string;
  metadata?: Record<string, unknown>;

  config?: {
    content_selector?: string;
    strip_boilerplate?: boolean;
    normalize_whitespace?: boolean;
    allowed_domains?: string[];
    max_pages?: number;
    request_timeout?: number;
    rate_limit?: number;
    user_agent?: string;
    deduplicate_content?: boolean;
  };

  processing?: {
    chunk_size?: number;
    chunk_overlap?: number;
    min_chunk_length?: number;
    max_chunk_length?: number;
    split_method?: 'paragraph' | 'semantic' | 'sentence' | 'recursive';
    preserve_headers?: boolean;
  };
}

export interface UploadDocumentRequest {
  file: File;
  auto_tag?: boolean;
  metadata?: Partial<Document>;
}

export interface TagSuggestion {
  tag: string;
  confidence: number;
}

export interface TagInventoryRow {
  tag: string;
  label?: string;
  locale?: string;
  resource_count?: number;
  source_count?: number;
  chunk_count?: number;
}

export interface TagInventoryResponse {
  tags: TagInventoryRow[];
  tag_counts: Record<string, number>;
  locale?: string;
}

export interface DashboardStats {
  total_documents: number;
  total_embeddings: number;
  documents_by_type: Record<string, number>;
  documents_by_language: Record<string, number>;
  recent_documents: Document[];
  warmup_status?: 'live' | 'fallback';
  warmup_message?: string;
}
