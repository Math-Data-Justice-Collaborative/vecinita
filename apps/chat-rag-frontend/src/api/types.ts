/** ChatRAG API types (openapi/chat-rag.yaml). */

export interface Source {
  chunk_id: string;
  document_id: string;
  title?: string | null;
  url?: string | null;
  score: number;
}

export type StreamEvent =
  | { token: string }
  | { sources: Source[] }
  | { done: true };

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}
