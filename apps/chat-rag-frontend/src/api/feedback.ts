import { requireChatApiConfig } from "../config";

export type FeedbackCategory = "bug" | "wrong_answer" | "suggestion" | "other";

export type FeedbackSubmitPayload = {
  category: FeedbackCategory;
  message: string;
  locale?: "en" | "es";
};

export type FeedbackSubmitResult = {
  id: string;
  created_at: string;
};

export async function submitFeedback(
  payload: FeedbackSubmitPayload,
): Promise<FeedbackSubmitResult> {
  const { baseUrl } = requireChatApiConfig();
  const response = await fetch(`${baseUrl}/api/v1/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Feedback failed (${String(response.status)})`);
  }
  return (await response.json()) as FeedbackSubmitResult;
}
