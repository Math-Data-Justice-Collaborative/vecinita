import type { Conversation } from "../hooks/useConversationStore";

const MAX_LABEL_LENGTH = 60;

/** Label a previous conversation by its first user message, truncated (RD-071). */
export function deriveConversationLabel(conversation: Conversation): string {
  const firstUser = conversation.messages.find((msg) => msg.role === "user");
  const content = firstUser ? firstUser.content : "";
  return content.length > MAX_LABEL_LENGTH
    ? `${content.slice(0, MAX_LABEL_LENGTH)}…`
    : content;
}
