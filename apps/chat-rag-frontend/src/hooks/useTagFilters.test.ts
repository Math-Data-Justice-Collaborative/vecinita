import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as browse from "../api/browse";
import { useTagFilters } from "./useTagFilters";

const housing: browse.TagFacet = {
  slug: "housing",
  label: "Housing",
  language: "en",
  document_count: 1,
};

describe("useTagFilters", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads tag facets on mount", async () => {
    vi.spyOn(browse, "fetchTags").mockResolvedValue({ tags: [housing] });

    const { result } = renderHook(() => useTagFilters());

    await waitFor(() => {
      expect(result.current.tags).toEqual([housing]);
    });
  });

  it("toggles a tag on and off", () => {
    vi.spyOn(browse, "fetchTags").mockResolvedValue({ tags: [housing] });

    const { result } = renderHook(() => useTagFilters());

    act(() => {
      result.current.toggle("housing");
    });
    expect(result.current.selected).toEqual(["housing"]);

    act(() => {
      result.current.toggle("housing");
    });
    expect(result.current.selected).toEqual([]);
  });

  it("keeps chat usable when tag loading fails", async () => {
    vi.spyOn(browse, "fetchTags").mockRejectedValue(new Error("500"));

    const { result } = renderHook(() => useTagFilters());

    await waitFor(() => {
      expect(result.current.tags).toEqual([]);
    });
  });

  it("does not set state after unmount", () => {
    let resolveTags: ((value: { tags: browse.TagFacet[] }) => void) | undefined;
    vi.spyOn(browse, "fetchTags").mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveTags = resolve;
        }),
    );

    const { unmount } = renderHook(() => useTagFilters());
    unmount();
    resolveTags?.({ tags: [housing] });
  });
});
