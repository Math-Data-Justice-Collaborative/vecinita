import type { TagFacet } from "../api/browse";
import type { Locale } from "../hooks/useLocale";

type TagFilterChipsProps = {
  tags: TagFacet[];
  selected: string[];
  locale: Locale;
  onToggle: (slug: string) => void;
};

export function TagFilterChips({ tags, selected, locale, onToggle }: TagFilterChipsProps) {
  const visibleTags = tags.filter((tag) => tag.language === locale);

  return (
    <div className="tag-chips" data-testid="tag-filter-chips" aria-label="Filter by topic">
      {visibleTags.map((tag) => {
        const active = selected.includes(tag.slug);
        return (
          <button
            key={tag.slug}
            type="button"
            className={active ? "tag-chip active" : "tag-chip"}
            aria-pressed={active}
            onClick={() => { onToggle(tag.slug); }}
          >
            {tag.label}
          </button>
        );
      })}
    </div>
  );
}
