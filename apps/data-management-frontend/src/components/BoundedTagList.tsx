import { TagBadge } from "@/components/TagBadge";
import type { TagInput } from "@/api/types";

const DEFAULT_MAX_VISIBLE = 3;

export type BoundedTagListProps = {
  tags: TagInput[];
  maxVisible?: number;
  moreTestId?: string | undefined;
};

/** Shows up to `maxVisible` tags; remainder as +N (EV-013 / #148). */
export function BoundedTagList({
  tags,
  maxVisible = DEFAULT_MAX_VISIBLE,
  moreTestId,
}: BoundedTagListProps) {
  if (tags.length === 0) {
    return null;
  }
  const visible = tags.slice(0, maxVisible);
  const overflow = tags.length - visible.length;
  const overflowLabels =
    overflow > 0
      ? tags
          .slice(maxVisible)
          .map((t) => t.label)
          .join(", ")
      : "";

  return (
    <div className="mt-1 flex max-w-full flex-wrap gap-1">
      {visible.map((tag) => (
        <TagBadge key={tag.slug} tag={tag} />
      ))}
      {overflow > 0 ? (
        <span
          className="inline-flex items-center rounded-md border border-border bg-muted px-1.5 py-0.5 text-xs text-muted-foreground contrast-more:border-foreground contrast-more:text-foreground"
          title={overflowLabels}
          aria-label={overflowLabels}
          data-testid={moreTestId}
        >
          +{overflow}
        </span>
      ) : null}
    </div>
  );
}
