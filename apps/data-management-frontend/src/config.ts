/** Build-time config per docs/config-spec.md (VITE_VECINITA_*). */

export const adminApiUrl = import.meta.env.VITE_VECINITA_ADMIN_API_URL;
export const modalProxyKey = import.meta.env.VITE_VECINITA_MODAL_PROXY_KEY;
export const corpusApiUrl = import.meta.env.VITE_VECINITA_CORPUS_API_URL;
export const corpusApiKey = import.meta.env.VITE_VECINITA_CORPUS_API_KEY;

export function requireAdminConfig(): { baseUrl: string; modalKey: string } {
  if (!adminApiUrl || !modalProxyKey) {
    throw new Error(
      "Set VITE_VECINITA_ADMIN_API_URL and VITE_VECINITA_MODAL_PROXY_KEY (see .env.example)",
    );
  }
  return { baseUrl: adminApiUrl.replace(/\/$/, ""), modalKey: modalProxyKey };
}

export function requireCorpusConfig(): { baseUrl: string; apiKey: string } {
  if (!corpusApiUrl || !corpusApiKey) {
    throw new Error(
      "Set VITE_VECINITA_CORPUS_API_URL and VITE_VECINITA_CORPUS_API_KEY (see .env.example)",
    );
  }
  return { baseUrl: corpusApiUrl.replace(/\/$/, ""), apiKey: corpusApiKey };
}
