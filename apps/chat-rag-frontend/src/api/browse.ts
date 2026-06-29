import { requireChatApiConfig } from "../config";

export type TagSummary = {
  slug: string;
  label: string;
};

export type DocumentBrowseItem = {
  document_id: string;
  title: string | null;
  url: string;
  language: string | null;
  tags: TagSummary[];
};

export type DocumentBrowsePage = {
  items: DocumentBrowseItem[];
  page: number;
  page_size: number;
  total: number;
};

export type TagFacet = {
  slug: string;
  label: string;
  language: string;
  document_count: number;
};

export type TagListResponse = {
  tags: TagFacet[];
};

export async function fetchDocuments(params: {
  tags?: string[] | undefined;
  q?: string | undefined;
  page?: number | undefined;
}): Promise<DocumentBrowsePage> {
  const { baseUrl } = requireChatApiConfig();
  const search = new URLSearchParams();
  params.tags?.forEach((tag) => {
    search.append("tags", tag);
  });
  if (params.q) {
    search.set("q", params.q);
  }
  if (params.page) {
    search.set("page", String(params.page));
  }
  const query = search.toString();
  const url = `${baseUrl}/api/v1/documents${query ? `?${query}` : ""}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Browse failed (${String(response.status)})`);
  }
  return (await response.json()) as DocumentBrowsePage;
}

export async function fetchTags(): Promise<TagListResponse> {
  const { baseUrl } = requireChatApiConfig();
  const response = await fetch(`${baseUrl}/api/v1/tags`);
  if (!response.ok) {
    throw new Error(`Tags failed (${String(response.status)})`);
  }
  return (await response.json()) as TagListResponse;
}
