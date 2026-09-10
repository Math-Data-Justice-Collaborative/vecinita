import { describe, expect, it } from "vitest";

import { JOB_STATUS_VARIANT } from "./jobStatusBadge";

describe("JOB_STATUS_VARIANT (UJ-098 / UX-7)", () => {
  it("maps statuses to distinct semantic variants", () => {
    expect(JOB_STATUS_VARIANT.completed).toBe("success");
    expect(JOB_STATUS_VARIANT.failed).toBe("destructive");
    expect(JOB_STATUS_VARIANT.running).toBe("secondary");
    expect(JOB_STATUS_VARIANT.pending).toBe("outline");
    expect(JOB_STATUS_VARIANT.cancelled).toBe("outline");
    expect(JOB_STATUS_VARIANT.completed).not.toBe(JOB_STATUS_VARIANT.cancelled);
    expect(JOB_STATUS_VARIANT.completed).not.toBe(JOB_STATUS_VARIANT.running);
  });
});
