const PLAYGROUND_CATALOG_FAMILIES = {
  families: [{ slug: "qwen2.5" }, { slug: "llama3.2" }],
};

const PLAYGROUND_CATALOG_TAGS: Record<
  string,
  { slug: string; tags: Array<{ model_id: string; available: boolean }> }
> = {
  "qwen2.5": {
    slug: "qwen2.5",
    tags: [
      { model_id: "qwen2.5:1.5b-instruct", available: true },
      { model_id: "qwen2.5:3b-instruct", available: false },
    ],
  },
  "llama3.2": {
    slug: "llama3.2",
    tags: [{ model_id: "llama3.2:3b", available: true }],
  },
};

export const PLAYGROUND_MODELS_LIST_BODY = {
  items: [
    { model_id: "qwen2.5:1.5b-instruct", available: true },
    { model_id: "llama3.2:3b", available: true },
  ],
};

export function mockPlaygroundApiFetch(
  url: string,
): { ok: true; json: () => Promise<unknown> } | null {
  if (url.includes("/internal/v1/models/ollama/catalog/")) {
    const slug = decodeURIComponent(
      url.split("/internal/v1/models/ollama/catalog/")[1] ?? "",
    );
    const body = PLAYGROUND_CATALOG_TAGS[slug] ?? { slug, tags: [] };
    return { ok: true, json: async () => body };
  }
  if (url.includes("/internal/v1/models/ollama/catalog")) {
    return { ok: true, json: async () => PLAYGROUND_CATALOG_FAMILIES };
  }
  if (
    url.includes("/internal/v1/models/ollama") &&
    !url.includes("/internal/v1/models/ollama/pull")
  ) {
    return { ok: true, json: async () => PLAYGROUND_MODELS_LIST_BODY };
  }
  return null;
}
