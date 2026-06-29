import { useCallback, useEffect, useState } from "react";

import { fetchTags, type TagFacet } from "../api/browse";

/**
 * Tag-facet fetch + selection, lifted to the app shell so the sidebar can render
 * the topic chips while {@link ChatPanel} consumes the selection for the ask
 * request. Tag chips are optional — chat still works if the fetch fails.
 */
export function useTagFilters(): {
  tags: TagFacet[];
  selected: string[];
  toggle: (slug: string) => void;
} {
  const [tags, setTags] = useState<TagFacet[]>([]);
  const [selected, setSelected] = useState<string[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function loadTags() {
      try {
        const response = await fetchTags();
        if (!cancelled) {
          setTags(response.tags);
        }
      } catch {
        // Tag chips are optional; chat still works without facets.
      }
    }
    void loadTags();
    return () => {
      cancelled = true;
    };
  }, []);

  const toggle = useCallback((slug: string) => {
    setSelected((current) =>
      current.includes(slug)
        ? current.filter((item) => item !== slug)
        : [...current, slug],
    );
  }, []);

  return { tags, selected, toggle };
}

export type TagFilters = ReturnType<typeof useTagFilters>;
