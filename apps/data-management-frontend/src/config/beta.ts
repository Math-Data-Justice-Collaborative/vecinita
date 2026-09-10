/**
 * Beta feedback URL for admin chrome (F86).
 * [Corpus: feature-list.md §F86]
 * [Spec: docs/acceptance-criteria.md §AC-BETA2]
 */
const DEFAULT_BETA_FEEDBACK_ISSUE_URL =
  "https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/374";

export function resolveBetaFeedbackIssueUrl(
  envValue: string | undefined = import.meta.env.VITE_BETA_FEEDBACK_ISSUE_URL,
): string {
  const trimmed = envValue?.trim();
  if (trimmed && /^https:\/\//.test(trimmed)) {
    return trimmed;
  }
  return DEFAULT_BETA_FEEDBACK_ISSUE_URL;
}

export const BETA_FEEDBACK_ISSUE_URL = resolveBetaFeedbackIssueUrl();
