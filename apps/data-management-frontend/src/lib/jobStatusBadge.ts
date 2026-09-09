import type { JobStatus } from "@/api/types";

/** Semantic badge variants for job lifecycle status (UJ-098 / UX-7). */
export type JobStatusBadgeVariant =
  "default" | "secondary" | "destructive" | "outline" | "success";

export const JOB_STATUS_VARIANT: Record<JobStatus, JobStatusBadgeVariant> = {
  pending: "outline",
  running: "secondary",
  completed: "success",
  failed: "destructive",
  cancelled: "outline",
};
