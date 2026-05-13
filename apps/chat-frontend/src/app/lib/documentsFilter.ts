import type { Source } from '../services/documentsService';

export function filterSources(sources: Source[], search: string, selectedTags: string[]): Source[] {
  const query = search.trim().toLowerCase();
  const normalizedSelectedTags = selectedTags.map((tag) => tag.toLowerCase());

  return sources.filter((source) => {
    const searchable =
      `${source.url} ${source.title ?? ''} ${source.source_domain ?? ''}`.toLowerCase();
    if (query && !searchable.includes(query)) {
      return false;
    }

    if (normalizedSelectedTags.length === 0) {
      return true;
    }

    const sourceTags = new Set((source.tags ?? []).map((tag) => tag.toLowerCase()));
    return normalizedSelectedTags.some((tag) => sourceTags.has(tag));
  });
}

export function toggleSelectedTag(selectedTags: string[], tag: string): string[] {
  return selectedTags.includes(tag)
    ? selectedTags.filter((item) => item !== tag)
    : [...selectedTags, tag];
}
