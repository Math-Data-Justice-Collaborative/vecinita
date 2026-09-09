import { describe, expect, it } from "vitest";

import { resolveBetaFeedbackIssueUrl } from "./beta";

describe("resolveBetaFeedbackIssueUrl", () => {
  it("uses default umbrella issue when env unset", () => {
    expect(resolveBetaFeedbackIssueUrl(undefined)).toBe(
      "https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/374",
    );
  });

  it("accepts https override", () => {
    expect(
      resolveBetaFeedbackIssueUrl(
        "https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/999",
      ),
    ).toBe(
      "https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/999",
    );
  });

  it("rejects non-https override", () => {
    expect(resolveBetaFeedbackIssueUrl("http://evil.example/x")).toBe(
      "https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/374",
    );
  });
});
