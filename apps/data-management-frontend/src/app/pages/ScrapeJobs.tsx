import { useEffect, useState } from "react";
import { ragApi } from "../api/rag-api";
import type { FrontendScrapeJob } from "../api/modal-types";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { RefreshCw, Clock, CheckCircle, XCircle } from "lucide-react";
import { toast } from "sonner";
import { Link } from "react-router";
import { Progress } from "../components/ui/progress";

export function ScrapeJobs() {
  const [jobs, setJobs] = useState<FrontendScrapeJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<string | null>(null);
  const [jobDetails, setJobDetails] = useState<FrontendScrapeJob | null>(null);

  useEffect(() => {
    loadJobs();
    // Poll for updates every 5 seconds
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadJobs = async () => {
    try {
      const data = await ragApi.getScrapeJobs();
      setJobs(data.jobs);
    } catch (error) {
      toast.error(`Failed to load jobs: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Jobs loading error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadJobDetails = async (jobId: string) => {
    try {
      const details = await ragApi.getScrapeStatus(jobId);
      setJobDetails(details);
      setSelectedJob(jobId);
    } catch (error) {
      toast.error(`Failed to load job details: ${error instanceof Error ? error.message : 'Unknown error'}`);
      console.error('Job details error:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'processing':
        return <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'queued':
        return <Clock className="w-5 h-5 text-yellow-600" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'destructive' | 'secondary' | 'outline'> = {
      completed: 'default',
      failed: 'destructive',
      processing: 'default',
      queued: 'secondary',
    };

    return (
      <Badge variant={variants[status] || 'outline'} className="capitalize">
        {status}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Scrape Jobs</h1>
          <p className="text-gray-500 mt-2">Monitor and manage URL scraping jobs</p>
        </div>
        <Button onClick={loadJobs} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Jobs List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              {jobs.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500">No scrape jobs yet</p>
                  <Link to="/add">
                    <Button className="mt-4">Start Scraping</Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  {jobs.map((job) => (
                    <div
                      key={job.job_id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        selectedJob === job.job_id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300'
                      }`}
                      onClick={() => loadJobDetails(job.job_id)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(job.status)}
                          <h3 className="font-medium text-gray-900 truncate max-w-md">
                            {job.url}
                          </h3>
                        </div>
                        {getStatusBadge(job.status)}
                      </div>
                      
                      <div className="flex items-center gap-4 text-sm text-gray-500 mt-2">
                        <span>Depth: {job.depth}</span>
                        <span>•</span>
                        <span>{new Date(job.created_at).toLocaleString()}</span>
                        {job.current_step && (
                          <>
                            <span>•</span>
                            <span className="capitalize">{job.current_step}</span>
                          </>
                        )}
                        {job.pages_scraped !== undefined && (
                          <>
                            <span>•</span>
                            <span>{job.pages_scraped} pages</span>
                          </>
                        )}
                      </div>

                      {job.status === 'processing' && job.progress !== undefined && (
                        <div className="mt-3">
                          <Progress value={job.progress} className="h-2" />
                          <p className="text-xs text-gray-500 mt-1">
                            {job.progress}% complete
                          </p>
                        </div>
                      )}

                      {job.error && (
                        <p className="text-sm text-red-600 mt-2">{job.error}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Job Details */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Job Details</CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedJob ? (
                <p className="text-sm text-gray-500">Select a job to view details</p>
              ) : jobDetails ? (
                <div className="space-y-4">
                  <div>
                    <span className="text-sm text-gray-500">Job ID</span>
                    <p className="font-mono text-xs break-all">{jobDetails.job_id}</p>
                  </div>

                  <div>
                    <span className="text-sm text-gray-500">Status</span>
                    <div className="mt-1">{getStatusBadge(jobDetails.status)}</div>
                    <p className="text-xs text-gray-500 mt-2 capitalize">
                      Backend stage: {jobDetails.current_step ?? jobDetails.backend_status}
                    </p>
                  </div>

                  {jobDetails.progress !== undefined && (
                    <div>
                      <span className="text-sm text-gray-500">Progress</span>
                      <div className="mt-2">
                        <Progress value={jobDetails.progress} className="h-2" />
                        <p className="text-xs text-gray-500 mt-1">
                          {jobDetails.progress}% complete
                        </p>
                      </div>
                    </div>
                  )}

                  {jobDetails.pages_scraped !== undefined && (
                    <div>
                      <span className="text-sm text-gray-500">Pages Scraped</span>
                      <p className="text-lg font-semibold">{jobDetails.pages_scraped}</p>
                    </div>
                  )}

                  {jobDetails.chunk_count !== undefined && (
                    <div>
                      <span className="text-sm text-gray-500">Chunks</span>
                      <p className="text-lg font-semibold">{jobDetails.chunk_count}</p>
                    </div>
                  )}

                  {jobDetails.embedding_count !== undefined && (
                    <div>
                      <span className="text-sm text-gray-500">Embeddings</span>
                      <p className="text-lg font-semibold">{jobDetails.embedding_count}</p>
                    </div>
                  )}

                  {jobDetails.updated_at && (
                    <div>
                      <span className="text-sm text-gray-500">Last Updated</span>
                      <p className="text-sm mt-1">{new Date(jobDetails.updated_at).toLocaleString()}</p>
                    </div>
                  )}

                  {jobDetails.documents_created && jobDetails.documents_created.length > 0 && (
                    <div>
                      <span className="text-sm text-gray-500">Created Documents</span>
                      <div className="mt-2 space-y-1">
                        {jobDetails.documents_created.map((docId: string) => (
                          <Link key={docId} to={`/document/${docId}`}>
                            <div className="text-xs p-2 bg-gray-50 rounded hover:bg-blue-50 hover:text-blue-600 cursor-pointer font-mono">
                              {docId}
                            </div>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {jobDetails.error && (
                    <div>
                      <span className="text-sm text-gray-500">Error</span>
                      <p className="text-sm text-red-600 mt-1 whitespace-pre-wrap">{jobDetails.error}</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Total Jobs</span>
                <span className="font-semibold">{jobs.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Completed</span>
                <span className="font-semibold text-green-600">
                  {jobs.filter(j => j.status === 'completed').length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Processing</span>
                <span className="font-semibold text-blue-600">
                  {jobs.filter(j => j.status === 'processing').length}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Failed</span>
                <span className="font-semibold text-red-600">
                  {jobs.filter(j => j.status === 'failed').length}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
