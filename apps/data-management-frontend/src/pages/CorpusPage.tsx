import { CorpusList } from "@/components/CorpusList";
import { JobForm } from "@/components/JobForm";

export function CorpusPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Corpus</h2>
        <p className="text-muted-foreground">Ingest URLs and manage documents.</p>
      </div>
      <JobForm />
      <CorpusList />
    </div>
  );
}
