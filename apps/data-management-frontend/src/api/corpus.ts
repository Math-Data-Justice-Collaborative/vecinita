import type { DocumentSummary } from "./types";

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
    throw new Error(detail || `List documents failed (${response.status})`);
  }
  return response.json() as Promise<DocumentSummary[]>;
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
    throw new Error(detail || `Delete failed (${response.status})`);
  }
}
