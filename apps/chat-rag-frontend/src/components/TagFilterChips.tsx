import type { TagFacet } from "../api/browse";

type TagFilterChipsProps = {
  tags: TagFacet[];
  selected: string[];
  onToggle: (slug: string) => void;
};

export function TagFilterChips({ tags, selected, onToggle }: TagFilterChipsProps) {
  const englishTags = tags.filter((tag) => tag.language === "en");

  return (
    <div className="tag-chips" data-testid="tag-filter-chips" aria-label="Filter by topic">
      {englishTags.map((tag) => {
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
