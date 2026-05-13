import { ragApi, type Document } from '../app/api/rag-api';

export interface CanonicalCorpusDocument extends Document {
  source_of_truth?: string;
  canonical_visibility_updated_at?: string;
}

export interface CanonicalCorpusListResponse {
  documents: CanonicalCorpusDocument[];
  total: number;
  page: number;
}

export async function listCanonicalCorpus(params?: {
  page?: number;
  limit?: number;
  search?: string;
  resource_type?: string;
  language?: string;
  tags?: string[];
}): Promise<CanonicalCorpusListResponse> {
  const response = await ragApi.getDocuments(params);
  return {
    ...response,
    documents: response.documents.map((doc) => ({
      ...doc,
      source_of_truth: (doc as Record<string, unknown>).source_of_truth as string | undefined,
      canonical_visibility_updated_at: (doc as Record<string, unknown>)
        .canonical_visibility_updated_at as string | undefined,
    })),
  };
}
