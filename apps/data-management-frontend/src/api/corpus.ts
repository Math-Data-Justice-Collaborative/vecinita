import type {
  ChunkDetail,
  CorpusTreeResponse,
  DocumentMetadataPatch,
  DocumentMetadataResponse,
  DocumentSummary,
  TagInput,
} from "./types";

export interface CorpusClientOptions {
  baseUrl: string;
  apiKey?: string | undefined;
  accessToken?: string | undefined;
}

export interface DocumentListPage {
  items: DocumentSummary[];
  page: number;
  page_size: number;
  total: number;
}

export interface ListDocumentsParams {
  page?: number;
  pageSize?: number;
  /** F76 — when true, only URL sources past the stale threshold (TC-258). */
  stale?: boolean;
}

function authHeaders(options: CorpusClientOptions): Record<string, string> {
  const bearer = options.accessToken ?? options.apiKey;
  if (!bearer) {
    throw new Error(
      "Corpus API requires Supabase session or VITE_VECINITA_CORPUS_API_KEY",
    );
  }
  return { Authorization: `Bearer ${bearer}` };
}

export async function listDocuments(
  options: CorpusClientOptions,
  params: ListDocumentsParams = {},
): Promise<DocumentListPage> {
  const page = params.page ?? 1;
  const pageSize = params.pageSize ?? 50;
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (params.stale === true) {
    query.set("stale", "true");
  }
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents?${query.toString()}`,
    {
      headers: authHeaders(options),
    },
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `List documents failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<DocumentListPage>;
}

export async function fetchCorpusTree(
  options: CorpusClientOptions,
): Promise<CorpusTreeResponse> {
  const response = await fetch(`${options.baseUrl}/internal/v1/corpus/tree`, {
    headers: authHeaders(options),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `Fetch corpus tree failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<CorpusTreeResponse>;
}

export async function listDocumentChunks(
  options: CorpusClientOptions,
  documentId: string,
): Promise<ChunkDetail[]> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/${documentId}/chunks`,
    {
      headers: authHeaders(options),
    },
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `List chunks failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<ChunkDetail[]>;
}

export async function listDocumentTags(
  options: CorpusClientOptions,
  documentId: string,
): Promise<TagInput[]> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/${documentId}/tags`,
    {
      headers: authHeaders(options),
    },
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `List document tags failed (${String(response.status)})`,
    );
  }
  const body = (await response.json()) as { tags: TagInput[] };
  return body.tags;
}

export async function patchDocumentMetadata(
  options: CorpusClientOptions,
  documentId: string,
  updates: DocumentMetadataPatch,
): Promise<DocumentMetadataResponse> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/${documentId}`,
    {
      method: "PATCH",
      headers: {
        ...authHeaders(options),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updates),
    },
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `Patch document metadata failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<DocumentMetadataResponse>;
}

export async function patchDocumentTags(
  options: CorpusClientOptions,
  documentId: string,
  tags: TagInput[],
): Promise<TagInput[]> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/${documentId}/tags`,
    {
      method: "PATCH",
      headers: {
        ...authHeaders(options),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ tags, source: "human" }),
    },
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `Patch document tags failed (${String(response.status)})`,
    );
  }
  const body = (await response.json()) as { tags: TagInput[] };
  return body.tags;
}

export async function patchChunkTags(
  options: CorpusClientOptions,
  chunkId: string,
  tags: TagInput[],
): Promise<TagInput[]> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/chunks/${chunkId}/tags`,
    {
      method: "PATCH",
      headers: {
        ...authHeaders(options),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ tags, source: "human" }),
    },
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `Patch chunk tags failed (${String(response.status)})`,
    );
  }
  const body = (await response.json()) as { tags: TagInput[] };
  return body.tags;
}

export async function retagDocument(
  options: CorpusClientOptions,
  documentId: string,
): Promise<string> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/${documentId}/retag`,
    {
      method: "POST",
      headers: authHeaders(options),
    },
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Retag failed (${String(response.status)})`);
  }
  const body = (await response.json()) as { job_id: string };
  return body.job_id;
}

/** F79 Refresh now — enqueue ``freshness_refresh`` with force=true (TC-274). */
export async function refreshDocument(
  options: CorpusClientOptions,
  documentId: string,
): Promise<string> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/${documentId}/refresh`,
    {
      method: "POST",
      headers: authHeaders(options),
    },
  );
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      detail || `Refresh document failed (${String(response.status)})`,
    );
  }
  const body = (await response.json()) as { job_id: string };
  return body.job_id;
}

export async function deleteDocument(
  options: CorpusClientOptions,
  documentId: string,
): Promise<void> {
  const response = await fetch(
    `${options.baseUrl}/internal/v1/documents/${documentId}`,
    {
      method: "DELETE",
      headers: authHeaders(options),
    },
  );
  if (response.status === 404) {
    throw new Error("Document not found");
  }
  if (!response.ok && response.status !== 204) {
    const detail = await response.text();
    throw new Error(detail || `Delete failed (${String(response.status)})`);
  }
}
