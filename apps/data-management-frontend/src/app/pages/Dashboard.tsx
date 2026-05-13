import { useEffect, useState } from "react";
import { ragApi, type DashboardStats } from "../api/rag-api";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { FileText, Globe, Database, TrendingUp } from "lucide-react";
import { Button } from "../components/ui/button";
import { Link } from "react-router";
import { toast } from "sonner";
import { useLocale } from "../i18n/LocaleContext";

export function Dashboard() {
  const { t } = useLocale();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statusBanner, setStatusBanner] = useState<{
    tone: 'warming' | 'success' | 'fallback';
    message: string;
  } | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    let warmupTimerTriggered = false;
    const warmupTimer = setTimeout(() => {
      warmupTimerTriggered = true;
      setStatusBanner({
        tone: 'warming',
        message: 'Backend is warming up. Retrying data fetch...',
      });
    }, 1200);

    try {
      const data = await ragApi.getStats();
      setStats(data);

      if (data.warmup_status === 'fallback') {
        setStatusBanner({
          tone: 'fallback',
          message: data.warmup_message || 'Using fallback stats while backend endpoints warm up.',
        });
      } else if (warmupTimerTriggered) {
        setStatusBanner({
          tone: 'success',
          message: 'Connected after warmup. Live data is now available.',
        });
      } else {
        setStatusBanner(null);
      }
    } catch (error) {
      setStatusBanner({
        tone: 'fallback',
        message: 'Stats unavailable. Showing fallback values while backend warms up.',
      });
      toast.error(`Stats temporarily unavailable (backend may be warming): ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Stats loading error:', error);
    } finally {
      clearTimeout(warmupTimer);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">{t('dashboard.title')}</h1>
        <p className="text-gray-500 mt-2">{t('dashboard.subtitle')}</p>
        <p className="text-sm text-gray-500 mt-3 max-w-3xl">{t('dashboard.disclosure')}</p>
      </div>

      {statusBanner && (
        <div
          className={
            statusBanner.tone === 'warming'
              ? 'mb-6 rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700'
              : statusBanner.tone === 'success'
                ? 'mb-6 rounded-md border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800'
                : 'mb-6 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900'
          }
        >
          {statusBanner.message}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Documents
            </CardTitle>
            <FileText className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_documents || 0}</div>
            <p className="text-xs text-gray-500 mt-1">In corpus</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Vector Embeddings
            </CardTitle>
            <Database className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_embeddings || 0}</div>
            <p className="text-xs text-gray-500 mt-1">Generated</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Websites
            </CardTitle>
            <Globe className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.documents_by_type?.website || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">Scraped URLs</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Documents
            </CardTitle>
            <TrendingUp className="w-4 h-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.documents_by_type?.document || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">Uploaded files</p>
          </CardContent>
        </Card>
      </div>

      {/* Resource Types Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader>
            <CardTitle>Resource Types</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.documents_by_type && Object.keys(stats.documents_by_type).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(stats.documents_by_type).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">{type}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{
                            width: `${(count / (stats.total_documents || 1)) * 100}%`,
                          }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-500 w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No data available</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Languages</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.documents_by_language && Object.keys(stats.documents_by_language).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(stats.documents_by_language).map(([language, count]) => (
                  <div key={language} className="flex items-center justify-between">
                    <span className="text-sm font-medium">{language}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{
                            width: `${(count / (stats.total_documents || 1)) * 100}%`,
                          }}
                        ></div>
                      </div>
                      <span className="text-sm text-gray-500 w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No data available</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Documents */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Documents</CardTitle>
          <Link to="/corpus">
            <Button variant="outline" size="sm">View All</Button>
          </Link>
        </CardHeader>
        <CardContent>
          {stats?.recent_documents && stats.recent_documents.length > 0 ? (
            <div className="space-y-4">
              {stats.recent_documents.map((doc) => (
                <Link key={doc.id} to={`/document/${doc.id}`}>
                  <div className="flex items-start gap-4 p-4 rounded-lg border border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-colors cursor-pointer">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate">{doc.title}</h3>
                      <p className="text-sm text-gray-500 line-clamp-2 mt-1">{doc.description}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {doc.resource_type}
                        </span>
                        <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                          {doc.format}
                        </span>
                        {doc.language && (
                          <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                            {doc.language}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm text-gray-500">No documents yet</p>
              <Link to="/add">
                <Button className="mt-4">Add Your First Document</Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
