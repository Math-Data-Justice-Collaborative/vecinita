import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useLoadTimeout } from "./useLoadTimeout";

describe("useLoadTimeout", () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("stays false while loading then flips after ms", () => {
    vi.useFakeTimers();
    const { result, rerender } = renderHook(
      ({ loading }) => useLoadTimeout(loading, 1000),
      { initialProps: { loading: true } },
    );
    expect(result.current).toBe(false);
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current).toBe(true);
    rerender({ loading: false });
    expect(result.current).toBe(false);
  });
});
