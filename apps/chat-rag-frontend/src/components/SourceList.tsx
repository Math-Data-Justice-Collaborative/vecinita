import { citationHref } from "vecinita-frontend-ui";

import type { Source } from "../api/types";
import type { Locale } from "../hooks/useLocale.types";
import { t } from "../i18n/messages";
import { dedupeSources } from "./dedupeSources";

interface SourceListProps {
  sources: Source[];
  locale: Locale;
}

function formatRelevancePercent(score: number): number {
  return Math.round(Math.min(1, Math.max(0, score)) * 100);
}

export function SourceList({ sources, locale }: SourceListProps) {
  const unique = dedupeSources(sources);
  if (unique.length === 0) {
    return null;
  }

  const tip = t(locale, "relevanceTip");

  return (
    <aside className="sources" data-testid="source-list">
      <h3>{t(locale, "sourcesHeading")}</h3>
      <ul>
        {unique.map((source) => {
          const href = citationHref(source.url);
          const label = source.title ?? source.url ?? t(locale, "corpusChunk");
          const percent = formatRelevancePercent(source.score);
          const scoreLabel = t(locale, "relevancePercent").replace(
            "{n}",
            String(percent),
          );
          return (
            <li key={source.chunk_id}>
              {href !== null ? (
                <a href={href} target="_blank" rel="noreferrer">
                  {source.title ?? href}
                </a>
              ) : (
                <span>{label || t(locale, "corpusChunk")}</span>
              )}{" "}
              <span
                className="source-score"
                title={tip}
                tabIndex={0}
                aria-label={`${scoreLabel}. ${tip}`}
              >
                {scoreLabel}
              </span>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
