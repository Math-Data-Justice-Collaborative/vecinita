import type { Source } from "../api/types";

interface SourceListProps {
  sources: Source[];
}

export function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <aside className="sources" data-testid="source-list">
      <h3>Sources</h3>
      <ul>
        {sources.map((source) => (
          <li key={source.chunk_id}>
            {source.url ? (
              <a href={source.url} target="_blank" rel="noreferrer">
                {source.title ?? source.url}
              </a>
            ) : (
              <span>{source.title ?? "Corpus chunk"}</span>
            )}
            <span className="source-score"> ({source.score.toFixed(2)})</span>
          </li>
        ))}
      </ul>
    </aside>
  );
}
