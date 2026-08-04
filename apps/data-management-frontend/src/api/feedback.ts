/** Admin Feedback list via DM GET /admin/feedback (F68). */

export type FeedbackItem = {
  id: string;
  created_at: string;
  category: string;
  message: string;
  locale: string | null;
};

export type FeedbackListResponse = {
  items: FeedbackItem[];
  page: number;
  page_size: number;
  total_count: number;
};

export type FeedbackClientOptions = {
  baseUrl: string;
  modalKey: string;
  accessToken?: string | undefined;
};

function headers(options: FeedbackClientOptions): Record<string, string> {
  const result: Record<string, string> = {
    "X-Vecinita-Proxy-Key": options.modalKey,
  };
  if (options.accessToken) {
    result["Authorization"] = `Bearer ${options.accessToken}`;
  }
  return result;
}

export async function fetchFeedbackList(
  options: FeedbackClientOptions,
  params?: { page?: number; page_size?: number; category?: string },
): Promise<FeedbackListResponse> {
  const query = new URLSearchParams({
    page: String(params?.page ?? 1),
    page_size: String(params?.page_size ?? 20),
  });
  if (params?.category) {
    query.set("category", params.category);
  }
  const response = await fetch(
    `${options.baseUrl}/admin/feedback?${query.toString()}`,
    { headers: headers(options) },
  );
  if (!response.ok) {
    throw new Error(`Feedback list failed (${String(response.status)})`);
  }
  return (await response.json()) as FeedbackListResponse;
}
