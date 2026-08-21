import type { Source } from "../api/types";

/** Collapse duplicate citations by URL (else document_id), keeping the max score. */
export function dedupeSources(sources: Source[]): Source[] {
  const bestByKey = new Map<string, Source>();
  for (const source of sources) {
    const key =
      source.url && source.url.trim() !== ""
        ? `url:${source.url}`
        : `doc:${source.document_id}`;
    const existing = bestByKey.get(key);
    if (existing === undefined || source.score > existing.score) {
      bestByKey.set(key, source);
    }
  }
  return [...bestByKey.values()];
}
