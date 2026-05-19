/** Build-time config per docs/config-spec.md (VITE_VECINITA_*). */

export const chatApiUrl = import.meta.env.VITE_VECINITA_CHAT_API_URL ?? "";

export function requireChatApiConfig(): { baseUrl: string } {
  if (!chatApiUrl) {
    throw new Error("Set VITE_VECINITA_CHAT_API_URL (see .env.example)");
  }
  return { baseUrl: chatApiUrl.replace(/\/$/, "") };
}
