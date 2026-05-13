import { parseJsonResponseOrThrow } from '../lib/responseParser';

export interface DocumentsCorpusSource {
  id?: string;
  url: string;
  title?: string;
  source_domain?: string;
  tags?: string[];
  download_url?: string;
  downloadable?: boolean;
  source_of_truth?: string;
  canonical_visibility_updated_at?: string;
}

export interface DocumentsCorpusOverview {
  sources: DocumentsCorpusSource[];
}

export async function fetchDocumentsCorpusOverview(
  apiBase: string
): Promise<DocumentsCorpusOverview> {
  const response = await fetch(`${apiBase}/documents/overview`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return parseJsonResponseOrThrow<DocumentsCorpusOverview>(response, '/documents/overview');
}
