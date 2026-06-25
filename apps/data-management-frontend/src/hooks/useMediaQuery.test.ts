import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useMediaQuery } from "./useMediaQuery";

describe("useMediaQuery", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns initial matchMedia result and reacts to change events", () => {
    let matches = true;
    let changeListener: (() => void) | undefined;

    vi.stubGlobal(
      "matchMedia",
      vi.fn((query: string) => ({
        get matches() {
          return matches;
        },
        media: query,
        addEventListener: (_event: string, listener: () => void) => {
          changeListener = listener;
        },
        removeEventListener: vi.fn(),
      })),
    );

    const { result } = renderHook(() => useMediaQuery("(min-width: 768px)"));
    expect(result.current).toBe(true);

    act(() => {
      matches = false;
      changeListener?.();
    });

    expect(result.current).toBe(false);
  });
});
