import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import type { TreeNode } from "@/api/types";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { useAdminT } from "@/hooks/useAdminT";
import { cn } from "@/lib/utils";

export interface CorpusTreeProps {
  roots: TreeNode[];
  selectedIds: Set<string>;
  onToggleSelect: (documentId: string) => void;
}

function documentCount(node: TreeNode): number | null {
  const count = node.counts?.["documents"];
  return typeof count === "number" ? count : null;
}

function TreeBranch({
  node,
  depth,
  selectedIds,
  onToggleSelect,
}: {
  node: TreeNode;
  depth: number;
  selectedIds: Set<string>;
  onToggleSelect: (documentId: string) => void;
}) {
  const tr = useAdminT();
  const hasChildren = (node.children?.length ?? 0) > 0;
  const [expanded, setExpanded] = useState(false);
  const count = documentCount(node);
  const expandLabel = expanded
    ? tr("admin.corpusTree.collapse", { label: node.label })
    : tr("admin.corpusTree.expand", { label: node.label });

  if (node.kind === "document") {
    const checked = selectedIds.has(node.id);
    return (
      <li
        role="treeitem"
        aria-selected={checked}
        className="flex items-center gap-2 py-1"
        style={{ paddingLeft: `${String(depth * 1.25)}rem` }}
      >
        <Checkbox
          checked={checked}
          onCheckedChange={() => {
            onToggleSelect(node.id);
          }}
          aria-label={tr("admin.corpusTree.selectDocument", {
            label: node.label,
          })}
        />
        <span className="text-sm font-medium">{node.label}</span>
        {node.status ? (
          <span
            className={cn(
              "rounded px-1.5 py-0.5 text-xs",
              node.status === "failed"
                ? "bg-destructive/15 text-destructive"
                : "bg-muted text-muted-foreground",
            )}
          >
            {node.status}
          </span>
        ) : null}
        {node.url ? (
          <span className="truncate text-xs text-muted-foreground">
            {node.url}
          </span>
        ) : null}
      </li>
    );
  }

  return (
    <li
      role="treeitem"
      aria-expanded={hasChildren ? expanded : undefined}
      className="list-none"
    >
      <div
        className="flex items-center gap-1 py-1"
        style={{ paddingLeft: `${String(depth * 1.25)}rem` }}
      >
        {hasChildren ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            aria-label={expandLabel}
            onClick={() => {
              setExpanded((prev) => !prev);
            }}
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        ) : (
          <span className="inline-block w-7" />
        )}
        <span className="text-sm font-semibold">{node.label}</span>
        {count !== null ? (
          <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
            {count}
          </span>
        ) : null}
      </div>
      {hasChildren && expanded ? (
        <ul role="group" className="m-0 list-none p-0">
          {(node.children ?? []).map((child) => (
            <TreeBranch
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedIds={selectedIds}
              onToggleSelect={onToggleSelect}
            />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function CorpusTree({
  roots,
  selectedIds,
  onToggleSelect,
}: CorpusTreeProps) {
  const tr = useAdminT();

  if (roots.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        {tr("admin.corpusTree.empty")}
      </p>
    );
  }

  return (
    <ul
      role="tree"
      aria-label={tr("admin.corpusTree.ariaLabel")}
      className="m-0 list-none p-0"
    >
      {roots.map((root) => (
        <TreeBranch
          key={root.id}
          node={root}
          depth={0}
          selectedIds={selectedIds}
          onToggleSelect={onToggleSelect}
        />
      ))}
    </ul>
  );
}
