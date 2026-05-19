/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_VECINITA_ADMIN_API_URL: string;
  readonly VITE_VECINITA_MODAL_PROXY_KEY: string;
  readonly VITE_VECINITA_CORPUS_API_URL: string;
  readonly VITE_VECINITA_CORPUS_API_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
