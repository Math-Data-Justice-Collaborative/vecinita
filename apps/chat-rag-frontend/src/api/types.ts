/** ChatRAG API types (openapi/chat-rag.yaml). */

export interface Source {
  chunk_id: string;
  document_id: string;
  title?: string | null;
  url?: string | null;
  score: number;
}

/** F65 / ADR-047 heuristic energy payload on ask + stream done. */
export interface EnergyEstimate {
  wh: number;
  g_co2e: number;
  method: "tdp_util_walltime_v1";
  advisory: string;
  car_km_equiv: number;
  car_m_equiv: number;
}

export type StreamEvent =
  | { token: string }
  | { sources: Source[] }
  | {
      done: true;
      cache_hit?: string;
      energy_estimate?: EnergyEstimate;
    };

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  energyEstimate?: EnergyEstimate;
}
