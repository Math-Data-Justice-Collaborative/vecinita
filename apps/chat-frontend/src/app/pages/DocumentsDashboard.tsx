import { useMemo, useState } from 'react';
import { ExternalLink, Link2, Download } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { resolveApiBase } from '../lib/apiBaseResolution';
import { fetchDownloadUrlForSource, type Source } from '../services/documentsService';
import { useDocumentsDashboardData } from '../hooks/useDocumentsDashboardData';
import { filterSources, toggleSelectedTag } from '../lib/documentsFilter';
import {
  canDownloadDocumentSource,
  canPerformDocumentMutation,
} from '../features/documents/actions';
import { DocumentsOutageState } from '../features/documents/components/DocumentsOutageState';

export { resolveApiBase };

const API_BASE = resolveApiBase(
  (import.meta.env.VITE_GATEWAY_URL as string | undefined) ||
    (import.meta.env.DEV ? '/api/v1' : 'http://localhost:8004/api/v1'),
  undefined,
  import.meta.env.VITE_BACKEND_URL as string | undefined
);

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border bg-card p-5 shadow-sm">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-xl font-semibold mt-1">{value}</p>
    </div>
  );
}

export default function DocumentsDashboard() {
  const { t } = useLanguage();
  const { overview, tagStats, loading, error } = useDocumentsDashboardData(API_BASE);
  const [search, setSearch] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [downloadingUrl, setDownloadingUrl] = useState<string | null>(null);
  const documentsReadOnly = !canPerformDocumentMutation();

  const filteredSources = useMemo(() => {
    if (!overview) return [];
    return filterSources(overview.sources, search, selectedTags);
  }, [overview, search, selectedTags]);

  const resolveDownloadUrl = async (source: Source): Promise<string> => {
    if (source.download_url) {
      return source.download_url;
    }

    try {
      return await fetchDownloadUrlForSource(API_BASE, source.url);
    } catch (err) {
      const message = err instanceof Error ? err.message : '';
      if (/^HTTP\s+\d+$/i.test(message)) {
        const status = message.split(/\s+/)[1];
        throw new Error(`${t('docsDownloadError')} (HTTP ${status})`);
      }
      throw new Error(t('docsNoDownloadAvailable'));
    }
  };

  const handleDownload = async (source: Source) => {
    try {
      setDownloadingUrl(source.url);
      const url = await resolveDownloadUrl(source);
      window.open(url, '_blank', 'noopener,noreferrer');
    } catch (downloadError) {
      alert(downloadError instanceof Error ? downloadError.message : t('docsDownloadFailed'));
    } finally {
      setDownloadingUrl(null);
    }
  };

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) => toggleSelectedTag(prev, tag));
  };

  if (loading) {
    return (
      <main className="flex flex-1 items-center justify-center">
        <p className="text-muted-foreground animate-pulse">{t('docsLoading')}</p>
      </main>
    );
  }

  if (error || !overview) {
    return (
      <DocumentsOutageState message={`${t('docsLoadFailed')}: ${error ?? t('docsUnknownError')}`} />
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold">{t('documentsTitle')}</h1>
        <p className="text-muted-foreground mt-1">{t('documentsSubtitle')}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label={t('docsTotalSources')} value={overview.sources.length} />
        <StatCard label={t('docsTotalTopics')} value={tagStats.length} />
        <StatCard label={t('docsVisibleResources')} value={filteredSources.length} />
      </div>

      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2 justify-between">
          <h2 className="text-lg font-semibold">{t('docsResources')}</h2>
          <input
            type="search"
            placeholder={t('docsSearchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded-md border bg-background px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-primary/40"
          />
        </div>

        <div className="rounded-xl border bg-muted/20 p-3 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium">{t('docsTopics')}</p>
            {selectedTags.length > 0 && (
              <button
                onClick={() => setSelectedTags([])}
                className="rounded border px-2 py-1 text-xs hover:bg-accent"
              >
                {t('docsClearFilters')}
              </button>
            )}
          </div>

          {tagStats.length === 0 ? (
            <p className="text-xs text-muted-foreground">{t('docsNoTopics')}</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {tagStats.map((item) => {
                const selected = selectedTags.includes(item.tag);
                return (
                  <button
                    key={item.tag}
                    onClick={() => toggleTag(item.tag)}
                    className={`rounded-full border px-2 py-1 text-xs transition-colors ${selected ? 'bg-primary text-primary-foreground border-primary' : 'hover:bg-accent'}`}
                    title={`${item.source_count} ${t('docsSourcesLabel')}`}
                  >
                    {item.tag} ({item.source_count})
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="rounded-xl border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/60 text-xs uppercase tracking-wide text-muted-foreground">
              <tr>
                <th className="px-4 py-3 text-left">{t('docsResource')}</th>
                <th className="px-4 py-3 text-center w-48">{t('docsActions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {filteredSources.length === 0 && (
                <tr>
                  <td colSpan={2} className="py-8 text-center text-muted-foreground">
                    {t('docsNoResults')}
                  </td>
                </tr>
              )}
              {filteredSources.map((source) => (
                <tr key={source.url} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Link2 size={14} className="text-muted-foreground shrink-0" />
                      {source.url.startsWith('http') ? (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline text-primary font-medium flex items-center gap-1 truncate max-w-sm"
                        >
                          {source.title || source.source_domain || source.url.split('/')[2]}
                          <ExternalLink size={12} className="shrink-0" />
                        </a>
                      ) : (
                        <span className="text-primary font-medium truncate max-w-sm block">
                          {source.title || source.source_domain || source.url}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground truncate max-w-sm mt-0.5 pl-6">
                      {source.url}
                    </p>
                    {(source.tags ?? []).length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2 pl-6">
                        {(source.tags ?? []).slice(0, 6).map((tag) => (
                          <span
                            key={`${source.url}-${tag}`}
                            className="rounded-full border px-2 py-0.5 text-[10px] text-muted-foreground"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-2">
                      {source.url.startsWith('http') && (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="rounded border px-2 py-1 text-xs hover:bg-accent"
                        >
                          {t('docsOpenSource')}
                        </a>
                      )}
                      {!source.url.startsWith('http') && canDownloadDocumentSource(source) && (
                        <button
                          onClick={() => handleDownload(source)}
                          disabled={downloadingUrl === source.url}
                          className="inline-flex items-center gap-1 rounded border px-2 py-1 text-xs hover:bg-accent disabled:opacity-50"
                        >
                          <Download size={12} />
                          {downloadingUrl === source.url ? '…' : t('docsDownload')}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {documentsReadOnly && (
          <p className="px-4 py-3 text-xs text-muted-foreground border-t">
            Documents tab is read-only and reflects canonical corpus data.
          </p>
        )}
      </div>
    </main>
  );
}
