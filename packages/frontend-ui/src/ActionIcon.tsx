import {
  type HTMLAttributes,
  type ReactNode,
  useEffect,
  useState,
} from "react";

import "./action-icon.css";

/** Motion → CSS class (defined in `action-icon.css`). */
export const ACTION_ICON_MOTION_CLASS = {
  spin: "vecinita-action-spin",
  pulse: "vecinita-action-pulse",
  shake: "vecinita-action-shake",
  press: "vecinita-action-press",
} as const;

export type ActionIconMotion = keyof typeof ACTION_ICON_MOTION_CLASS;

export interface ActionIconProps extends HTMLAttributes<HTMLSpanElement> {
  children: ReactNode;
  /** When true, apply motion class and set `aria-busy`. */
  pending?: boolean | undefined;
  /** Animation style while pending. Default: `spin` (refresh). */
  motion?: ActionIconMotion | undefined;
  /**
   * Override `prefers-reduced-motion` detection (tests / forced reduce).
   * When true, pending still sets `aria-busy` but skips animation classes.
   */
  reducedMotion?: boolean | undefined;
}

function readPrefersReducedMotion(): boolean {
  if (
    typeof window === "undefined" ||
    typeof window.matchMedia !== "function"
  ) {
    return false;
  }
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Shared action-bound icon wrapper (F66 / #104).
 * Applies spin/pulse/shake/press while `pending`; honors reduced motion.
 */
export function ActionIcon({
  children,
  pending = false,
  motion = "spin",
  reducedMotion: reducedMotionProp,
  className,
  ...rest
}: ActionIconProps) {
  const [mediaReduced, setMediaReduced] = useState(readPrefersReducedMotion);

  useEffect(() => {
    if (reducedMotionProp !== undefined) {
      return;
    }
    if (
      typeof window === "undefined" ||
      typeof window.matchMedia !== "function"
    ) {
      return;
    }
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => {
      setMediaReduced(mq.matches);
    };
    sync();
    mq.addEventListener("change", sync);
    return () => {
      mq.removeEventListener("change", sync);
    };
  }, [reducedMotionProp]);

  const reduced =
    reducedMotionProp !== undefined ? reducedMotionProp : mediaReduced;
  const animate = pending && !reduced;
  const motionClass = animate ? ACTION_ICON_MOTION_CLASS[motion] : undefined;
  const merged = [className, motionClass].filter(Boolean).join(" ");

  return (
    <span
      {...rest}
      className={merged.length > 0 ? merged : undefined}
      aria-busy={pending ? true : undefined}
      data-action-icon-motion={motion}
      data-action-icon-pending={pending ? "true" : "false"}
    >
      {children}
    </span>
  );
}
