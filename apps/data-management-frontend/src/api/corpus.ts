import type { ChunkDetail, DocumentSummary, TagInput } from "./types";

export interface CorpusClientOptions {
  baseUrl: string;
  apiKey: string;
}

function authHeaders(apiKey: string): HeadersInit {
  return { Authorization: `Bearer ${apiKey}` };
}

export async function listDocuments(options: CorpusClientOptions): Promise<DocumentSummary[]> {
  const response = await fetch(`${options.baseUrl}/internal/v1/documents`, {
    headers: authHeaders(options.apiKey),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `List documents failed (${String(response.status)})`);
  }
  return response.json() as Promise<DocumentSummary[]>;
}

export async function listDocumentChunks(
  options: CorpusClientOptions,
  documentId: string,
): Promise<ChunkDetail[]> {
  const response = await fetch(`${options.baseUrl}/internal/v1/documents/${documentId}/chunks`, {
    headers: authHeaders(options.apiKey),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `List chunks failed (${String(response.status)})`);
  }
  return response.json() as Promise<ChunkDetail[]>;
}

export async function listDocumentTags(
  options: CorpusClientOptions,
  documentId: string,
): Promise<TagInput[]> {
  const response = await fetch(`${options.baseUrl}/internal/v1/documents/${documentId}/tags`, {
    headers: authHeaders(options.apiKey),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `List document tags failed (${String(response.status)})`);
  }
  const body = (await response.json()) as { tags: TagInput[] };
  return body.tags;
}

export async function patchDocumentTags(
  options: CorpusClientOptions,
  documentId: string,
  tags: TagInput[],
): Promise<TagInput[]> {
  const response = await fetch(`${options.baseUrl}/internal/v1/documents/${documentId}/tags`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${options.apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tags, source: "human" }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Patch document tags failed (${String(response.status)})`);
  }
  const body = (await response.json()) as { tags: TagInput[] };
  return body.tags;
}

export async function patchChunkTags(
  options: CorpusClientOptions,
  chunkId: string,
  tags: TagInput[],
): Promise<TagInput[]> {
  const response = await fetch(`${options.baseUrl}/internal/v1/chunks/${chunkId}/tags`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${options.apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tags, source: "human" }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Patch chunk tags failed (${String(response.status)})`);
  }
  const body = (await response.json()) as { tags: TagInput[] };
  return body.tags;
}

export async function retagDocument(
  options: CorpusClientOptions,
  documentId: string,
): Promise<string> {
  const response = await fetch(`${options.baseUrl}/internal/v1/documents/${documentId}/retag`, {
    method: "POST",
    headers: authHeaders(options.apiKey),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Retag failed (${String(response.status)})`);
  }
  const body = (await response.json()) as { job_id: string };
  return body.job_id;
}

export async function deleteDocument(
  options: CorpusClientOptions,
  documentId: string,
): Promise<void> {
  const response = await fetch(`${options.baseUrl}/internal/v1/documents/${documentId}`, {
    method: "DELETE",
    headers: authHeaders(options.apiKey),
  });
  if (response.status === 404) {
    throw new Error("Document not found");
  }
  if (!response.ok && response.status !== 204) {
    const detail = await response.text();
    throw new Error(detail || `Delete failed (${String(response.status)})`);
  }
}
