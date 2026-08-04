import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import {
  type ComponentPropsWithoutRef,
  type ReactElement,
  type ReactNode,
} from "react";

import "./tooltip.css";

export type TooltipProviderProps = ComponentPropsWithoutRef<
  typeof TooltipPrimitive.Provider
>;

/** App-level provider — wrap once near the root (F67 / #106). */
export function TooltipProvider({
  delayDuration = 200,
  skipDelayDuration = 0,
  ...props
}: TooltipProviderProps) {
  return (
    <TooltipPrimitive.Provider
      delayDuration={delayDuration}
      skipDelayDuration={skipDelayDuration}
      {...props}
    />
  );
}

export interface TooltipProps {
  /** Localized tooltip body (i18n at call site). */
  content: ReactNode;
  /** Single focusable/hoverable child (Radix `asChild`). */
  children: ReactElement;
  open?: boolean | undefined;
  defaultOpen?: boolean | undefined;
  onOpenChange?: ((open: boolean) => void) | undefined;
  side?: "top" | "right" | "bottom" | "left" | undefined;
  /** Extra class on the content surface. */
  className?: string | undefined;
}

/**
 * Accessible shared Tooltip (Radix). Supplements `aria-label`; shows on hover
 * and keyboard focus. Styles work without Tailwind (ChatRAG).
 */
export function Tooltip({
  content,
  children,
  open,
  defaultOpen,
  onOpenChange,
  side = "top",
  className,
}: TooltipProps) {
  const contentClass = ["vecinita-tooltip-content", className]
    .filter(Boolean)
    .join(" ");

  return (
    <TooltipPrimitive.Root
      {...(open !== undefined ? { open } : {})}
      {...(defaultOpen !== undefined ? { defaultOpen } : {})}
      {...(onOpenChange !== undefined ? { onOpenChange } : {})}
    >
      <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          className={contentClass}
          side={side}
          sideOffset={4}
          data-testid="tooltip-content"
        >
          {content}
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
    </TooltipPrimitive.Root>
  );
}
