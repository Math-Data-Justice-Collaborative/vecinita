/** Best-effort pre-warm of Modal LLM + embedding when the chat UI mounts (S001 T11). */
export function prewarmChatServices(baseUrl: string): void {
  void fetch(`${baseUrl}/api/v1/warm`, { method: "POST" }).catch(() => {
    // Pre-warm is optional; cold-start retry UX handles remaining failures.
  });
}
