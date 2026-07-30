import { BackfillForm } from "@/components/BackfillForm";
import { CorpusList } from "@/components/CorpusList";
import { JobForm } from "@/components/JobForm";
import { RebuildForm } from "@/components/RebuildForm";
import { RebuildPromoteForm } from "@/components/RebuildPromoteForm";
import { useAdminT } from "@/hooks/useAdminT";

export function CorpusPage() {
  const tr = useAdminT();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          {tr("admin.corpus.title")}
        </h2>
        <p className="text-muted-foreground">{tr("admin.corpus.subtitle")}</p>
      </div>
      <JobForm />
      <RebuildForm />
      <RebuildPromoteForm />
      <BackfillForm />
      <CorpusList />
    </div>
  );
}
