import { useEffect, useState } from 'react';
import {
  fetchDocumentsOverview,
  fetchDocumentTagStats,
  type Overview,
  type TagStat,
} from '../services/documentsService';

interface UseDocumentsDashboardDataResult {
  overview: Overview | null;
  tagStats: TagStat[];
  loading: boolean;
  error: string | null;
}

export function useDocumentsDashboardData(apiBase: string): UseDocumentsDashboardDataResult {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [tagStats, setTagStats] = useState<TagStat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCancelled = false;

    const load = async () => {
      try {
        const [overviewData, tags] = await Promise.all([
          fetchDocumentsOverview(apiBase),
          fetchDocumentTagStats(apiBase),
        ]);

        if (isCancelled) {
          return;
        }

        setOverview(overviewData);
        setTagStats(tags);
      } catch (err) {
        if (isCancelled) {
          return;
        }

        setOverview(null);
        setTagStats([]);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    void load();

    return () => {
      isCancelled = true;
    };
  }, [apiBase]);

  return {
    overview,
    tagStats,
    loading,
    error,
  };
}
