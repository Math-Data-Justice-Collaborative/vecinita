import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/config", () => ({
  idleTimeoutMinutes: () => 2,
  idleWarningSeconds: () => 10,
}));

import { useIdleTimeout } from "./useIdleTimeout";

describe("useIdleTimeout", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("clears timers when disabled and runs timeout on signOutNow", async () => {
    const onTimeout = vi.fn();
    const { result, rerender } = renderHook(
      ({ enabled }) => useIdleTimeout(enabled, onTimeout),
      { initialProps: { enabled: true } },
    );

    act(() => {
      window.dispatchEvent(new Event("click"));
    });
    act(() => {
      vi.advanceTimersByTime(500);
      window.dispatchEvent(new Event("click"));
    });

    act(() => {
      result.current.signOutNow();
    });
    await act(async () => {
      await Promise.resolve();
    });
    expect(onTimeout).toHaveBeenCalled();

    rerender({ enabled: false });
    expect(result.current.showWarning).toBe(false);
  });

  it("shows warning countdown, decrements, and stays signed in on activity", () => {
    const onTimeout = vi.fn();
    const { result } = renderHook(() => useIdleTimeout(true, onTimeout));

    act(() => {
      vi.advanceTimersByTime(110_000);
    });
    expect(result.current.showWarning).toBe(true);
    expect(result.current.secondsRemaining).toBe(10);

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(result.current.secondsRemaining).toBeLessThan(10);

    act(() => {
      result.current.staySignedIn();
    });
    expect(result.current.showWarning).toBe(false);

    act(() => {
      Object.defineProperty(document, "visibilityState", {
        configurable: true,
        get: () => "visible",
      });
      document.dispatchEvent(new Event("visibilitychange"));
    });
    expect(result.current.showWarning).toBe(false);
  });

  it("runs timeout when warning countdown completes", () => {
    const onTimeout = vi.fn();
    renderHook(() => useIdleTimeout(true, onTimeout));

    act(() => {
      vi.advanceTimersByTime(110_000);
    });
    act(() => {
      vi.advanceTimersByTime(10_000);
    });
    expect(onTimeout).toHaveBeenCalled();
  });

  it("clears countdown interval when unmounting during warning", () => {
    const onTimeout = vi.fn();
    const { unmount } = renderHook(() => useIdleTimeout(true, onTimeout));
    act(() => {
      vi.advanceTimersByTime(110_000);
    });
    unmount();
  });

  it("clears an existing countdown when warning restarts", () => {
    const onTimeout = vi.fn();
    let warningCallback: (() => void) | undefined;
    const originalSetTimeout = global.setTimeout;
    const clearIntervalSpy = vi.spyOn(global, "clearInterval");
    const setTimeoutSpy = vi
      .spyOn(global, "setTimeout")
      .mockImplementation((handler, timeout) => {
        if (timeout === 110_000) {
          warningCallback = handler as () => void;
          return 1 as unknown as ReturnType<typeof setTimeout>;
        }
        return originalSetTimeout(handler, timeout);
      });

    renderHook(() => useIdleTimeout(true, onTimeout));

    act(() => {
      warningCallback?.();
      warningCallback?.();
    });

    expect(clearIntervalSpy).toHaveBeenCalled();
    setTimeoutSpy.mockRestore();
    clearIntervalSpy.mockRestore();
  });

  it("ignores visibility changes when the document is hidden", () => {
    const onTimeout = vi.fn();
    renderHook(() => useIdleTimeout(true, onTimeout));

    act(() => {
      Object.defineProperty(document, "visibilityState", {
        configurable: true,
        get: () => "hidden",
      });
      document.dispatchEvent(new Event("visibilitychange"));
    });

    expect(onTimeout).not.toHaveBeenCalled();
  });
});
