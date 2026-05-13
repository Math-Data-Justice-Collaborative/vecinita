/**
 * Test-time / release-time checks: main SPA bundles must not ship Modal web hosts
 * or Modal token keys in `VITE_*` values (SC-005, feature 007).
 */

const FORBIDDEN_VALUE_SUBSTRINGS = ['modal.run', 'modal.com'] as const;

export function collectForbiddenViteEnvIssues(env: Record<string, string | undefined>): string[] {
  const issues: string[] = [];
  for (const [key, raw] of Object.entries(env)) {
    if (!key.startsWith('VITE_')) {
      continue;
    }
    if (key.toUpperCase().includes('MODAL_TOKEN')) {
      issues.push(`${key}: VITE_* keys must not embed MODAL_TOKEN (server-side only).`);
      continue;
    }
    const val = (raw ?? '').trim();
    if (!val) {
      continue;
    }
    const lower = val.toLowerCase();
    for (const frag of FORBIDDEN_VALUE_SUBSTRINGS) {
      if (lower.includes(frag)) {
        issues.push(`${key}: value must not include "${frag}" in the main frontend bundle.`);
      }
    }
  }
  return issues;
}
