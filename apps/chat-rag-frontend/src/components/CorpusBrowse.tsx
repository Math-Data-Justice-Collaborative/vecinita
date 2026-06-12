import { FormEvent, useEffect, useState } from "react";

import {
  fetchDocuments,
  fetchTags,
  type DocumentBrowseItem,
  type TagFacet,
} from "../api/browse";
import { useLocale } from "../hooks/useLocale";
import { t } from "../i18n/messages";

type CorpusBrowseProps = {
  onNavigateHome: () => void;
};

export function CorpusBrowse({ onNavigateHome }: CorpusBrowseProps) {
  const [items, setItems] = useState<DocumentBrowseItem[]>([]);
  const [tags, setTags] = useState<TagFacet[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize, setPageSize] = useState(20);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const { locale } = useLocale();

  useEffect(() => {
    let cancelled = false;
    async function loadTags() {
      try {
        const response = await fetchTags();
        if (!cancelled) {
          setTags(response.tags);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t(locale, "loadTagsFailed"));
        }
      }
    }
    void loadTags();
    return () => {
      cancelled = true;
    };
  }, [locale]);

  useEffect(() => {
    let cancelled = false;
    async function loadDocuments() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchDocuments({
          tags: selectedTags.length > 0 ? selectedTags : undefined,
          q: query.trim() || undefined,
          page,
        });
        if (!cancelled) {
          setItems(response.items);
          setTotal(response.total);
          setPageSize(response.page_size);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : t(locale, "loadDocumentsFailed"));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void loadDocuments();
    return () => {
      cancelled = true;
    };
  }, [selectedTags, query, page, locale]);

  function toggleTag(slug: string) {
    setPage(1);
    setSelectedTags((current) =>
      current.includes(slug) ? current.filter((item) => item !== slug) : [...current, slug],
    );
  }

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setPage(1);
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <section className="corpus-browse" aria-label={t(locale, "corpusBrowseLabel")}>
      <div className="corpus-toolbar">
        <button type="button" className="secondary" onClick={onNavigateHome}>
          {t(locale, "backToChat")}
        </button>
      </div>

      <form className="corpus-search" onSubmit={handleSearch}>
        <label htmlFor="corpus-search">{t(locale, "searchLabel")}</label>
        <input
          id="corpus-search"
          type="search"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setPage(1);
          }}
          placeholder={t(locale, "searchPlaceholder")}
        />
      </form>

      <div className="tag-chips" data-testid="browse-tag-chips">
        {tags
          .filter((tag) => tag.language === locale)
          .map((tag) => {
            const active = selectedTags.includes(tag.slug);
            return (
              <button
                key={tag.slug}
                type="button"
                className={active ? "tag-chip active" : "tag-chip"}
                aria-pressed={active}
                onClick={() => { toggleTag(tag.slug); }}
              >
                {tag.label}
              </button>
            );
          })}
      </div>

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {loading ? <p role="status">{t(locale, "loadingDocuments")}</p> : null}

      <ul className="corpus-list" data-testid="corpus-list">
        {items.map((item) => (
          <li key={item.document_id} className="corpus-item">
            <h2>{item.title ?? t(locale, "untitledDocument")}</h2>
            <p className="corpus-tags">
              {item.tags.map((tag) => tag.label).join(", ") || t(locale, "noTags")}
            </p>
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              data-testid="corpus-source-link"
            >
              {t(locale, "openSource")}
            </a>
          </li>
        ))}
      </ul>

      <div className="corpus-pagination">
        <button
          type="button"
          className="secondary"
          disabled={page <= 1}
          onClick={() => { setPage((current) => Math.max(1, current - 1)); }}
        >
          {t(locale, "previous")}
        </button>
        <span>{t(locale, "pagination", page, totalPages, total)}</span>
        <button
          type="button"
          className="secondary"
          disabled={page >= totalPages}
          onClick={() => { setPage((current) => current + 1); }}
        >
          {t(locale, "next")}
        </button>
      </div>
    </section>
  );
}
