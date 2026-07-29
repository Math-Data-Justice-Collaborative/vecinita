/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_VECINITA_CHAT_API_URL: string;
  readonly VITE_WRWC_DONATE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
