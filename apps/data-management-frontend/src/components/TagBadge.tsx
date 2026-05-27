import { cn } from "@/lib/utils";
import type { TagInput } from "@/api/types";

interface TagBadgeProps {
  tag: TagInput;
}

export function TagBadge({ tag }: TagBadgeProps) {
  const isLlm = tag.source === "llm";
  return (
    <span
      data-testid={`tag-${tag.slug}`}
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        isLlm
          ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
          : "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
      )}
    >
      {tag.label}
    </span>
  );
}
