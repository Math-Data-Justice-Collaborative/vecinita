import { renderHook, act } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { usePathname } from "./usePathname";

describe("usePathname", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("reads the initial window pathname", () => {
    window.history.replaceState({}, "", "/corpus");
    const { result } = renderHook(() => usePathname());
    expect(result.current.pathname).toBe("/corpus");
    window.history.replaceState({}, "", "/");
  });

  it("navigate updates pathname via history.pushState", () => {
    const { result } = renderHook(() => usePathname());
    act(() => {
      result.current.navigate("/corpus");
    });
    expect(result.current.pathname).toBe("/corpus");
    expect(window.location.pathname).toBe("/corpus");
    act(() => {
      result.current.navigate("/");
    });
  });

  it("syncs pathname on popstate", () => {
    const { result } = renderHook(() => usePathname());
    window.history.pushState({}, "", "/corpus");
    act(() => {
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(result.current.pathname).toBe("/corpus");
    window.history.replaceState({}, "", "/");
  });

  it("syncs a second hook instance when another navigates", () => {
    const first = renderHook(() => usePathname());
    const second = renderHook(() => usePathname());
    act(() => {
      first.result.current.navigate("/corpus");
    });
    expect(second.result.current.pathname).toBe("/corpus");
    expect(window.location.pathname).toBe("/corpus");
    window.history.replaceState({}, "", "/");
  });
});
