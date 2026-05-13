/**
 * Data Management API Client
 *
 * This client supports scraper jobs and corpus operations. All HTTP traffic uses
 * {@link browserDmHttpApiBase}, which MUST resolve to the **data-management API**
 * origin only (see `scraper-config.ts` / `VITE_DM_API_BASE_URL`), never a direct scraper
 * `*.modal.run` host or the chat gateway for job CRUD.
 */

import {
  clampNumber,
  isModalTerminalStatus,
  mapModalStatusToFrontendStatus,
  remoteListJobId,
  type ModalJobStatus,
  type ScrapeJobListItem,
} from './modal-types';
import type {
  DashboardStats,
  Document,
  FrontendScrapeJob,
  KnownScrapeJob,
  ModalCreateJobResponse,
  ModalJobStatusResponse,
  ModalListJobsResponse,
  ModalScrapeJobRequest,
  ScrapeRequest,
  TagInventoryResponse,
  TagInventoryRow,
  TagSuggestion,
  UploadDocumentRequest,
} from './types';
import { normalizeUpstreamErrorMessage } from './operatorUpstreamErrors';
import { browserDmHttpApiBase, scraperJobsApiRoot, scraperRuntimeConfig } from './scraper-config';
import { getCurrentAuthToken } from '../auth/apiKeyAuth';

function dmHttpBase(): string {
  return browserDmHttpApiBase();
}

function isRagMockMode(): boolean {
  return !dmHttpBase();
}
const KNOWN_SCRAPE_JOBS_STORAGE_KEY = 'vecinita.scrape-jobs';
const REQUEST_TIMEOUT_MS = 15_000;
const REQUEST_MAX_RETRIES = 3;

const generateMockId = () => Math.random().toString(36).substr(2, 9);

let mockDocuments: Document[] = isRagMockMode() ? [
  {
    id: '1',
    title: 'RI Food Bank Community Resources',
    description: 'Directory of food assistance programs across Rhode Island',
    url: 'https://rifoodbank.org/community-resources',
    resource_type: 'website',
    format: 'HTML',
    language: 'English',
    organization: 'Rhode Island Food Bank',
    embedding_status: 'completed',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    updated_at: new Date(Date.now() - 86400000).toISOString(),
    tags: ['food-assistance', 'community', 'resources'],
  },
  {
    id: '2',
    title: 'Sample Research Paper',
    description: 'Academic paper on machine learning applications',
    url: 'https://example.com/paper.pdf',
    resource_type: 'document',
    format: 'PDF',
    language: 'English',
    organization: 'University Research',
    embedding_status: 'completed',
    created_at: new Date(Date.now() - 172800000).toISOString(),
    updated_at: new Date(Date.now() - 172800000).toISOString(),
    tags: ['research', 'machine-learning', 'academic'],
  },
] : [];

class RAGApiClient {
  private normalizeTagInventory(payload: unknown): TagInventoryResponse {
    const result: TagInventoryResponse = {
      tags: [],
      tag_counts: {},
    };

    if (!payload || typeof payload !== 'object') {
      return result;
    }

    const data = payload as {
      tags?: unknown;
      tag_counts?: Record<string, number>;
      locale?: string;
    };

    if (typeof data.locale === 'string' && data.locale.trim()) {
      result.locale = data.locale;
    }

    if (data.tag_counts && typeof data.tag_counts === 'object') {
      result.tag_counts = Object.fromEntries(
        Object.entries(data.tag_counts).map(([tag, count]) => [tag, Number(count) || 0]),
      );
    }

    if (Array.isArray(data.tags)) {
      result.tags = data.tags
        .map((entry) => {
          if (typeof entry === 'string') {
            const count = result.tag_counts[entry] || 0;
            return {
              tag: entry,
              label: entry,
              resource_count: count,
              source_count: count,
            } satisfies TagInventoryRow;
          }

          if (!entry || typeof entry !== 'object') {
            return null;
          }

          const row = entry as Record<string, unknown>;
          const tag = typeof row.tag === 'string' ? row.tag : '';
          if (!tag) {
            return null;
          }

          const resourceCount = Number(row.resource_count ?? row.source_count ?? result.tag_counts[tag] ?? 0) || 0;
          if (!(tag in result.tag_counts)) {
            result.tag_counts[tag] = resourceCount;
          }

          return {
            tag,
            label: typeof row.label === 'string' && row.label.trim() ? row.label : tag,
            locale: typeof row.locale === 'string' ? row.locale : result.locale,
            resource_count: resourceCount,
            source_count: Number(row.source_count ?? resourceCount) || resourceCount,
            chunk_count: Number(row.chunk_count ?? 0) || 0,
          } satisfies TagInventoryRow;
        })
        .filter((entry): entry is TagInventoryRow => entry !== null);
    }

    if (result.tags.length === 0 && Object.keys(result.tag_counts).length > 0) {
      result.tags = Object.entries(result.tag_counts).map(([tag, count]) => ({
        tag,
        label: tag,
        resource_count: count,
        source_count: count,
        locale: result.locale,
      }));
    }

    return result;
  }

  private shouldRetryStatus(status: number): boolean {
    return status === 408 || status === 429 || status >= 500;
  }

  private classifyFetchError(error: unknown): { retryable: boolean; message: string } {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return {
        retryable: true,
        message:
          'The request timed out (network or Modal cold start). Wait a few seconds and retry, or check worker load.',
      };
    }

    if (error instanceof TypeError) {
      return {
        retryable: true,
        message: 'Could not reach the data-management API. Check your network or VPN.',
      };
    }

    if (error instanceof Error) {
      return { retryable: false, message: error.message };
    }

    return { retryable: false, message: 'Unknown request failure' };
  }

  private async delayForRetry(attempt: number): Promise<void> {
    const baseDelayMs = 500;
    const backoff = Math.min(baseDelayMs * 2 ** attempt, 4_000);
    await new Promise((resolve) => {
      setTimeout(resolve, backoff);
    });
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit,
    baseUrl?: string,
  ): Promise<T> {
    const headers = new Headers(options?.headers);
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    if (!headers.has('Authorization')) {
      const authToken = getCurrentAuthToken();
      if (authToken) {
        headers.set('Authorization', `Bearer ${authToken}`);
      }
    }

    let lastError: Error | null = null;
    const resolvedBase = (baseUrl ?? dmHttpBase()).replace(/\/+$/, '');

    for (let attempt = 0; attempt <= REQUEST_MAX_RETRIES; attempt += 1) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, REQUEST_TIMEOUT_MS);

      try {
        const response = await fetch(`${resolvedBase}${endpoint}`, {
          ...options,
          headers,
          signal: controller.signal,
        });

        if (!response.ok) {
          const httpStatus = response.status > 0 ? response.status : 500;
          const errorBody = await response.json().catch(() => ({}));
          const message = normalizeUpstreamErrorMessage(httpStatus, errorBody);
          const retryableStatus = this.shouldRetryStatus(httpStatus);

          if (!retryableStatus || attempt === REQUEST_MAX_RETRIES) {
            throw new Error(message);
          }

          lastError = new Error(message);
          await this.delayForRetry(attempt);
          continue;
        }

        return response.json();
      } catch (error) {
        const classified = this.classifyFetchError(error);
        if (!classified.retryable || attempt === REQUEST_MAX_RETRIES) {
          throw new Error(classified.message);
        }

        lastError = new Error(classified.message);
        await this.delayForRetry(attempt);
      } finally {
        clearTimeout(timeoutId);
      }
    }

    throw lastError ?? new Error('API request failed');
  }

  private buildStatsFromDocuments(documents: Document[]): DashboardStats {
    const documents_by_type: Record<string, number> = {};
    const documents_by_language: Record<string, number> = {};

    documents.forEach((doc) => {
      documents_by_type[doc.resource_type] = (documents_by_type[doc.resource_type] || 0) + 1;
      documents_by_language[doc.language] = (documents_by_language[doc.language] || 0) + 1;
    });

    return {
      total_documents: documents.length,
      total_embeddings: documents.filter((d) => d.embedding_status === 'completed').length * 10,
      documents_by_type,
      documents_by_language,
      recent_documents: documents.slice(0, 5),
    };
  }

  private buildStatsFromJobs(jobs: FrontendScrapeJob[]): DashboardStats {
    const documents_by_type: Record<string, number> = {
      website: jobs.length,
    };

    const documents_by_language: Record<string, number> = {
      Unknown: jobs.length,
    };

    const recent_documents: Document[] = jobs.slice(0, 5).map((job) => ({
      id: `job-${job.job_id}`,
      title: `Scraped: ${job.url}`,
      description: `Scrape job ${job.job_id} (${job.status})`,
      url: job.url,
      resource_type: 'website',
      format: 'HTML',
      language: 'Unknown',
      organization: 'Vecinita Scraper',
      embedding_status: job.status === 'completed' ? 'completed' : 'processing',
      created_at: job.created_at,
      updated_at: job.updated_at || job.created_at,
      tags: [],
    }));

    const embeddingCount = jobs.reduce((sum, job) => sum + (job.embedding_count || 0), 0);

    return {
      total_documents: jobs.length,
      total_embeddings: embeddingCount,
      documents_by_type,
      documents_by_language,
      recent_documents,
    };
  }

  private getKnownScrapeJobs(): KnownScrapeJob[] {
    if (typeof window === 'undefined') {
      return [];
    }

    try {
      const value = window.localStorage.getItem(KNOWN_SCRAPE_JOBS_STORAGE_KEY);
      if (!value) {
        return [];
      }

      const parsed = JSON.parse(value) as KnownScrapeJob[];
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  private rememberScrapeJob(job: KnownScrapeJob): void {
    if (typeof window === 'undefined') {
      return;
    }

    const jobs = this.getKnownScrapeJobs().filter((item) => item.job_id !== job.job_id);
    jobs.unshift(job);
    window.localStorage.setItem(
      KNOWN_SCRAPE_JOBS_STORAGE_KEY,
      JSON.stringify(jobs.slice(0, 50)),
    );
  }

  private inferProgress(status: ModalJobStatus, progressPct: number | null): number {
    if (typeof progressPct === 'number') {
      return progressPct;
    }

    const statusProgress: Record<ModalJobStatus, number> = {
      pending: 5,
      validating: 10,
      crawling: 25,
      extracting: 40,
      processing: 55,
      chunking: 70,
      embedding: 85,
      storing: 95,
      completed: 100,
      failed: 100,
      cancelled: 100,
    };

    return statusProgress[status] ?? 0;
  }

  private mapStatusResponseToFrontendJob(
    status: ModalJobStatusResponse,
    knownJob?: KnownScrapeJob,
  ): FrontendScrapeJob {
    return {
      job_id: status.job_id,
      url: status.url ?? knownJob?.url ?? 'Unknown URL',
      depth: knownJob?.depth ?? 0,
      status: mapModalStatusToFrontendStatus(status.status),
      backend_status: status.status,
      created_at: status.created_at,
      updated_at: status.updated_at,
      completed_at: isModalTerminalStatus(status.status) ? status.updated_at : undefined,
      progress: this.inferProgress(status.status, status.progress_pct),
      current_step: status.current_step ?? status.status,
      pages_scraped: status.crawl_url_count,
      chunk_count: status.chunk_count,
      embedding_count: status.embedding_count,
      documents_created: [],
      error: status.error_message ?? undefined,
    };
  }

  private buildModalScrapeJobRequest(request: ScrapeRequest): ModalScrapeJobRequest {
    const maxSizeTokens = request.processing?.chunk_size
      ? clampNumber(request.processing.chunk_size, 200, 4096)
      : undefined;
    const chunkOverlapRatio =
      request.processing?.chunk_size && request.processing?.chunk_overlap
        ? clampNumber(request.processing.chunk_overlap / request.processing.chunk_size, 0, 0.5)
        : undefined;

    return {
      url: request.url,
      user_id: request.user_id || scraperRuntimeConfig.defaultUserId,
      crawl_config: {
        max_depth: clampNumber(request.depth + 1, 1, 10),
        timeout_seconds: request.config?.request_timeout
          ? clampNumber(request.config.request_timeout, 10, 600)
          : undefined,
        headless: true,
        wait_for_content: true,
        include_links: request.depth > 0,
        include_images: false,
      },
      chunking_config: maxSizeTokens
        ? {
            min_size_tokens: clampNumber(Math.floor(maxSizeTokens * 0.5), 100, maxSizeTokens),
            max_size_tokens: maxSizeTokens,
            overlap_ratio: chunkOverlapRatio,
            split_by_sentence: request.processing?.split_method !== 'paragraph',
          }
        : undefined,
      metadata: {
        auto_tag: request.auto_tag ?? false,
        source: 'vecinita-data-management-frontend',
        ...(request.metadata ?? {}),
      },
    };
  }

  // ============ CORPUS MANAGEMENT ============

  /**
   * GET /documents
   * Retrieve all documents in the corpus
   */
  async getDocuments(params?: {
    page?: number;
    limit?: number;
    search?: string;
    resource_type?: string;
    language?: string;
    tags?: string[];
  }): Promise<{ documents: Document[]; total: number; page: number }> {
    if (isRagMockMode()) {
      const filteredDocuments = mockDocuments.filter(doc => {
        if (params?.search && !doc.title.toLowerCase().includes(params.search.toLowerCase())) return false;
        if (params?.resource_type && doc.resource_type !== params.resource_type) return false;
        if (params?.language && doc.language !== params.language) return false;
        if (params?.tags && !params.tags.every(tag => doc.tags?.includes(tag))) return false;
        return true;
      });
      const total = filteredDocuments.length;
      const page = params?.page || 1;
      const limit = params?.limit || 10;
      const documents = filteredDocuments.slice((page - 1) * limit, page * limit);
      return { documents, total, page };
    }

    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.append('page', params.page.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.resource_type) queryParams.append('resource_type', params.resource_type);
    if (params?.language) queryParams.append('language', params.language);
    if (params?.tags) queryParams.append('tags', params.tags.join(','));

    return this.request(`/documents?${queryParams.toString()}`);
  }

  /**
   * GET /documents/:id
   * Retrieve a specific document by ID
   */
  async getDocument(id: string): Promise<Document> {
    if (isRagMockMode()) {
      const document = mockDocuments.find(doc => doc.id === id);
      if (!document) throw new Error('Document not found');
      return document;
    }

    return this.request(`/documents/${id}`);
  }

  /**
   * POST /documents
   * Create a new document manually
   */
  async createDocument(document: Omit<Document, 'id' | 'created_at' | 'updated_at'>): Promise<Document> {
    if (isRagMockMode()) {
      const newDocument: Document = {
        ...document,
        id: generateMockId(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      mockDocuments.push(newDocument);
      return newDocument;
    }

    return this.request('/documents', {
      method: 'POST',
      body: JSON.stringify(document),
    });
  }

  /**
   * PUT /documents/:id
   * Update an existing document
   */
  async updateDocument(id: string, updates: Partial<Document>): Promise<Document> {
    if (isRagMockMode()) {
      const documentIndex = mockDocuments.findIndex(doc => doc.id === id);
      if (documentIndex === -1) throw new Error('Document not found');
      const updatedDocument: Document = {
        ...mockDocuments[documentIndex],
        ...updates,
        updated_at: new Date().toISOString(),
      };
      mockDocuments[documentIndex] = updatedDocument;
      return updatedDocument;
    }

    return this.request(`/documents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  /**
   * DELETE /documents/:id
   * Delete a document from the corpus and vector database
   */
  async deleteDocument(id: string): Promise<{ success: boolean }> {
    if (isRagMockMode()) {
      const documentIndex = mockDocuments.findIndex(doc => doc.id === id);
      if (documentIndex === -1) throw new Error('Document not found');
      mockDocuments.splice(documentIndex, 1);
      return { success: true };
    }

    return this.request(`/documents/${id}`, {
      method: 'DELETE',
    });
  }

  /**
   * DELETE /documents
   * Bulk delete documents
   */
  async deleteDocuments(ids: string[]): Promise<{ success: boolean; deleted_count: number }> {
    if (isRagMockMode()) {
      const deletedCount = mockDocuments.filter(doc => ids.includes(doc.id)).length;
      mockDocuments = mockDocuments.filter(doc => !ids.includes(doc.id));
      return { success: true, deleted_count: deletedCount };
    }

    return this.request('/documents/bulk-delete', {
      method: 'DELETE',
      body: JSON.stringify({ ids }),
    });
  }

  // ============ URL SCRAPING ============

  /**
   * POST /jobs
   * Submit a scrape job to the Modal scraper control plane
   */
  async scrapeUrl(request: ScrapeRequest): Promise<{
    job_id: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    created_at: string;
    url: string;
  }> {
    const jobsBase = scraperJobsApiRoot();
    if (!jobsBase) {
      const created_at = new Date().toISOString();
      const job_id = generateMockId();
      this.rememberScrapeJob({ job_id, url: request.url, depth: request.depth, created_at });
      return {
        job_id,
        status: 'queued',
        created_at,
        url: request.url,
      };
    }

    const payload = this.buildModalScrapeJobRequest(request);
    const response = await this.request<ModalCreateJobResponse>(
      '',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      jobsBase,
    );

    this.rememberScrapeJob({
      job_id: response.job_id,
      url: response.url || request.url,
      depth: request.depth,
      created_at: response.created_at,
    });

    return {
      job_id: response.job_id,
      status: mapModalStatusToFrontendStatus(response.status),
      created_at: response.created_at,
      url: response.url || request.url,
    };
  }

  /**
   * GET /jobs/:job_id
   * Get the status of a scraping job
   */
  async getScrapeStatus(jobId: string): Promise<FrontendScrapeJob> {
    const jobsBase = scraperJobsApiRoot();
    if (!jobsBase) {
      const knownJob = this.getKnownScrapeJobs().find((job) => job.job_id === jobId);
      if (!knownJob) {
        throw new Error('Job not found');
      }

      return {
        job_id: knownJob.job_id,
        url: knownJob.url,
        depth: knownJob.depth,
        status: 'queued',
        backend_status: 'pending',
        created_at: knownJob.created_at,
        progress: 5,
        current_step: 'pending',
        pages_scraped: 0,
        chunk_count: 0,
        embedding_count: 0,
        documents_created: [],
      };
    }

    const knownJob = this.getKnownScrapeJobs().find((job) => job.job_id === jobId);
    const response = await this.request<ModalJobStatusResponse>(`/${jobId}`, undefined, jobsBase);
    return this.mapStatusResponseToFrontendJob(response, knownJob);
  }

  /**
   * GET /jobs
   * Get all scraping jobs
   */
  async getScrapeJobs(): Promise<{
    jobs: FrontendScrapeJob[];
  }> {
    const jobsBase = scraperJobsApiRoot();
    if (!jobsBase) {
      return {
        jobs: this.getKnownScrapeJobs().map((job) => ({
          job_id: job.job_id,
          url: job.url,
          depth: job.depth,
          status: 'queued',
          backend_status: 'pending',
          created_at: job.created_at,
          progress: 5,
          current_step: 'pending',
          pages_scraped: 0,
          chunk_count: 0,
          embedding_count: 0,
          documents_created: [],
        })),
      };
    }

    const knownJobs = this.getKnownScrapeJobs();
    const queryParams = new URLSearchParams({
      user_id: scraperRuntimeConfig.defaultUserId,
      limit: '100',
    });

    let remoteJobs: ModalListJobsResponse['jobs'] = [];
    try {
      const response = await this.request<ModalListJobsResponse>(
        `?${queryParams.toString()}`,
        undefined,
        jobsBase,
      );
      remoteJobs = response.jobs ?? [];
    } catch (error) {
      if (knownJobs.length === 0) {
        throw error;
      }
    }

    const jobsById = new Map<string, FrontendScrapeJob>();
    for (const remoteJob of remoteJobs) {
      const row = remoteJob as ScrapeJobListItem & {
        progress_pct?: number | null;
        current_step?: string | null;
      };
      const remoteId = remoteListJobId(row);
      const knownJob = knownJobs.find((job) => job.job_id === remoteId);
      if (!remoteId || !row.status || !row.created_at) {
        continue;
      }

      const backendStatus = row.status as ModalJobStatus;
      jobsById.set(remoteId, {
        job_id: remoteId,
        url: row.url ?? knownJob?.url ?? 'Unknown URL',
        depth: knownJob?.depth ?? 0,
        status: mapModalStatusToFrontendStatus(backendStatus),
        backend_status: backendStatus,
        created_at: row.created_at,
        updated_at: row.updated_at ?? undefined,
        completed_at: row.updated_at ?? undefined,
        progress: this.inferProgress(backendStatus, row.progress_pct ?? null),
        current_step: row.current_step ?? row.status,
        pages_scraped: row.crawl_url_count ?? 0,
        chunk_count: row.chunk_count ?? 0,
        embedding_count: row.embedding_count ?? 0,
        documents_created: [],
        error: row.error_message ?? undefined,
      });
    }

    const jobIdsToHydrate = knownJobs
      .filter((job) => {
        const existing = jobsById.get(job.job_id);
        return !existing || existing.status === 'queued' || existing.status === 'processing';
      })
      .map((job) => job.job_id);

    const hydratedJobs = await Promise.allSettled(
      jobIdsToHydrate.map((jobId) => this.getScrapeStatus(jobId)),
    );

    for (const result of hydratedJobs) {
      if (result.status === 'fulfilled') {
        jobsById.set(result.value.job_id, result.value);
      }
    }

    return {
      jobs: [...jobsById.values()].sort(
        (left, right) => new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
      ),
    };
  }

  async cancelScrapeJob(jobId: string): Promise<{
    job_id: string;
    previous_status: string;
    new_status: string;
  }> {
    const jobsBase = scraperJobsApiRoot();
    if (!jobsBase) {
      return { job_id: jobId, previous_status: 'pending', new_status: 'cancelled' };
    }
    return this.request(
      `/${jobId}/cancel`,
      {
        method: 'POST',
      },
      jobsBase,
    );
  }

  // ============ DOCUMENT UPLOAD ============

  /**
   * POST /upload
   * Upload a document file (PDF, DOCX, TXT, etc.)
   */
  async uploadDocument(request: UploadDocumentRequest): Promise<{
    document_id: string;
    status: 'processing' | 'completed';
  }> {
    const formData = new FormData();
    formData.append('file', request.file);
    if (request.auto_tag !== undefined) {
      formData.append('auto_tag', request.auto_tag.toString());
    }
    if (request.metadata) {
      formData.append('metadata', JSON.stringify(request.metadata));
    }

    const response = await fetch(`${dmHttpBase()}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(error.message || 'Upload failed');
    }

    return response.json();
  }

  // ============ AUTO-TAGGING ============

  /**
   * POST /tags/auto-generate
   * Generate tags for a document using AI
   */
  async autoGenerateTags(documentId: string): Promise<{
    document_id: string;
    suggestions: TagSuggestion[];
    metadata: Partial<Document>;
  }> {
    return this.request('/tags/auto-generate', {
      method: 'POST',
      body: JSON.stringify({ document_id: documentId }),
    });
  }

  /**
   * POST /tags/apply
   * Apply suggested tags to a document
   */
  async applyTags(documentId: string, tags: string[], metadata?: Partial<Document>): Promise<Document> {
    return this.request('/tags/apply', {
      method: 'POST',
      body: JSON.stringify({ document_id: documentId, tags, metadata }),
    });
  }

  /**
   * GET /tags
   * Get all unique tags in the corpus
   */
  async getAllTags(locale?: string): Promise<TagInventoryResponse> {
    if (isRagMockMode()) {
      const tag_counts: Record<string, number> = {};
      mockDocuments.forEach(doc => {
        doc.tags?.forEach(tag => {
          tag_counts[tag] = (tag_counts[tag] || 0) + 1;
        });
      });
      
      // Add some common category tags
      const categoryTags = [
        'food-assistance', 'housing', 'healthcare', 'legal-aid',
        'low-income', 'seniors', 'immigrants', 'statewide',
        'Providence', 'free', 'appointment-required'
      ];
      categoryTags.forEach(tag => {
        if (!tag_counts[tag]) {
          tag_counts[tag] = Math.floor(Math.random() * 5) + 1;
        }
      });
      
      return {
        tags: Object.keys(tag_counts).map((tag) => ({
          tag,
          label: tag,
          resource_count: tag_counts[tag],
          source_count: tag_counts[tag],
          locale: locale || 'en',
        })),
        tag_counts,
        locale: locale || 'en',
      };
    }

    const params = new URLSearchParams();
    if (locale) {
      params.append('locale', locale);
    }

    const raw = await this.request<unknown>(`/tags${params.toString() ? `?${params.toString()}` : ''}`);
    return this.normalizeTagInventory(raw);
  }

  // ============ VECTOR DATABASE OPERATIONS ============

  /**
   * POST /embeddings/generate
   * Generate embeddings for a document
   */
  async generateEmbeddings(documentId: string): Promise<{
    document_id: string;
    status: 'completed' | 'failed';
    vector_count: number;
  }> {
    return this.request('/embeddings/generate', {
      method: 'POST',
      body: JSON.stringify({ document_id: documentId }),
    });
  }

  /**
   * POST /embeddings/search
   * Semantic search in the vector database
   */
  async semanticSearch(query: string, filters?: {
    resource_type?: string[];
    language?: string;
    tags?: string[];
    limit?: number;
  }): Promise<{
    results: Array<{
      document: Document;
      score: number;
      matched_chunks: string[];
    }>;
  }> {
    return this.request('/embeddings/search', {
      method: 'POST',
      body: JSON.stringify({ query, filters }),
    });
  }

  /**
   * GET /stats
   * Get corpus statistics
   */
  async getStats(): Promise<DashboardStats> {
    if (isRagMockMode()) {
      return this.buildStatsFromDocuments(mockDocuments);
    }

    try {
      const [documentsResult, jobsResult] = await Promise.allSettled([
        this.getDocuments({ page: 1, limit: 100 }),
        this.getScrapeJobs(),
      ]);

      const documents =
        documentsResult.status === 'fulfilled' ? documentsResult.value.documents : [];
      const jobs = jobsResult.status === 'fulfilled' ? jobsResult.value.jobs : [];

      if (documents.length > 0) {
        const liveStats = this.buildStatsFromDocuments(documents);
        if (jobsResult.status === 'rejected') {
          liveStats.warmup_status = 'fallback';
          liveStats.warmup_message = 'Scraper jobs are warming up; showing document-only stats.';
        } else {
          liveStats.warmup_status = 'live';
        }
        return liveStats;
      }

      if (jobs.length > 0) {
        const jobStats = this.buildStatsFromJobs(jobs);
        jobStats.warmup_status = 'fallback';
        jobStats.warmup_message = 'Document endpoint unavailable; showing scraper-job derived stats.';
        return jobStats;
      }

      const fallbackStats = this.buildStatsFromDocuments(mockDocuments);
      fallbackStats.warmup_status = 'fallback';
      fallbackStats.warmup_message = 'Backend returned no stats sources; showing local fallback values.';
      return fallbackStats;
    } catch (error) {
      console.warn('Falling back to local stats due to backend stats endpoint failure', error);
      const fallbackStats = this.buildStatsFromDocuments(mockDocuments);
      fallbackStats.warmup_status = 'fallback';
      fallbackStats.warmup_message = 'Backend is warming up; showing local fallback values.';
      return fallbackStats;
    }
  }
}

export const ragApi = new RAGApiClient();

/** Re-export DTO surface for pages/tests that import types from `rag-api`. */
export type {
  DashboardStats,
  Document,
  FrontendScrapeJob,
  KnownScrapeJob,
  ModalCreateJobResponse,
  ModalJobStatusResponse,
  ModalListJobsResponse,
  ModalScrapeJobRequest,
  ScrapeRequest,
  TagInventoryResponse,
  TagInventoryRow,
  TagSuggestion,
  UploadDocumentRequest,
} from './types';