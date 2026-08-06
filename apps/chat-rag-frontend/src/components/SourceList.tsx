import { citationHref } from "vecinita-frontend-ui";

import type { Source } from "../api/types";
import type { Locale } from "../hooks/useLocale.types";
import { t } from "../i18n/messages";

interface SourceListProps {
  sources: Source[];
  locale: Locale;
}

export function SourceList({ sources, locale }: SourceListProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <aside className="sources" data-testid="source-list">
      <h3>{t(locale, "sourcesHeading")}</h3>
      <ul>
        {sources.map((source) => {
          const href = citationHref(source.url);
          const label = source.title ?? source.url ?? t(locale, "corpusChunk");
          return (
            <li key={source.chunk_id}>
              {href !== null ? (
                <a href={href} target="_blank" rel="noreferrer">
                  {source.title ?? href}
                </a>
              ) : (
                <span>{label || t(locale, "corpusChunk")}</span>
              )}
              <span className="source-score"> ({source.score.toFixed(2)})</span>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
