import { useCallback, useState } from "react";

import { createJob, getJob, parseUrlsInput } from "../api/jobs";
import type { Job } from "../api/types";
import { requireAdminConfig } from "../config";

const POLL_MS = 2000;
const TERMINAL: Job["status"][] = ["completed", "failed"];

export interface JobFormProps {
  onJobUpdate?: (job: Job) => void;
}

export function JobForm({ onJobUpdate }: JobFormProps) {
  const [urlsText, setUrlsText] = useState("");
  const [chunkSize, setChunkSize] = useState("256");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<Job | null>(null);

  const pollUntilDone = useCallback(
    async (jobId: string) => {
      const client = requireAdminConfig();
      let job = await getJob(client, jobId);
      setActiveJob(job);
      onJobUpdate?.(job);

      while (!TERMINAL.includes(job.status)) {
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
        job = await getJob(client, jobId);
        setActiveJob(job);
        onJobUpdate?.(job);
      }
    },
    [onJobUpdate],
  );

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setActiveJob(null);

    const urls = parseUrlsInput(urlsText);
    if (urls.length === 0) {
      setError("Enter at least one URL (one per line).");
      return;
    }

    const parsedChunk = Number(chunkSize);
    if (!Number.isFinite(parsedChunk) || parsedChunk < 64) {
      setError("Chunk size must be at least 64 tokens.");
      return;
    }

    setBusy(true);
    try {
      const client = requireAdminConfig();
      const created = await createJob(client, urls, parsedChunk);
      await pollUntilDone(created.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingest failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section aria-labelledby="ingest-heading">
      <h2 id="ingest-heading">Ingest URLs</h2>
      <form onSubmit={(e) => void handleSubmit(e)}>
        <label htmlFor="urls">Public URLs (one per line)</label>
        <textarea
          id="urls"
          rows={5}
          value={urlsText}
          onChange={(e) => setUrlsText(e.target.value)}
          placeholder="https://example.org/community/page"
          disabled={busy}
        />
        <label htmlFor="chunk-size">Chunk size (tokens)</label>
        <input
          id="chunk-size"
          type="number"
          min={64}
          value={chunkSize}
          onChange={(e) => setChunkSize(e.target.value)}
          disabled={busy}
        />
        <button type="submit" disabled={busy}>
          {busy ? "Running…" : "Submit ingest job"}
        </button>
      </form>
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}
      {activeJob ? (
        <div className="job-status" data-testid="job-status">
          <p>
            Job <code>{activeJob.job_id}</code>: <strong>{activeJob.status}</strong>
          </p>
          {activeJob.error_code ? (
            <p className="error">
              {activeJob.error_code}: {activeJob.error_message}
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
