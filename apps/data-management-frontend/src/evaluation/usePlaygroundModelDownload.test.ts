import { act, renderHook, waitFor } from "@testing-library/react";
import { MODEL_PULL_POLL_INTERVAL_MS } from "./playgroundModelDownloadContext";
import { createElement, type ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as adminApi from "@/api/admin";

import {
  PlaygroundModelDownloadProvider,
  firstAvailableModelId,
  modelOptionLabel,
  usePlaygroundModelDownload,
} from "./usePlaygroundModelDownload";

function providerWrapper({ children }: { children: ReactNode }) {
  return createElement(PlaygroundModelDownloadProvider, null, children);
}

describe("usePlaygroundModelDownload helpers", () => {
  it("firstAvailableModelId returns null when no model is available", () => {
    expect(
      firstAvailableModelId([
        { model_id: "qwen2.5:3b-instruct", available: false },
      ]),
    ).toBeNull();
  });

  it("modelOptionLabel appends not-downloaded suffix for unavailable models", () => {
    expect(
      modelOptionLabel(
        { model_id: "qwen2.5:3b-instruct", available: false },
        "(not downloaded)",
      ),
    ).toBe("qwen2.5:3b-instruct (not downloaded)");
  });
});

describe("usePlaygroundModelDownload hook", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("throws when used outside PlaygroundModelDownloadProvider", () => {
    expect(() => renderHook(() => usePlaygroundModelDownload())).toThrow(
      /PlaygroundModelDownloadProvider/,
    );
  });

  it("loadFamilyTags surfaces non-Error tag failures", async () => {
    vi.spyOn(adminApi, "fetchPlaygroundModels").mockResolvedValue({ items: [] });
    vi.spyOn(adminApi, "fetchPlaygroundCatalogFamilies").mockResolvedValue({
      families: [],
    });
    vi.spyOn(adminApi, "fetchPlaygroundCatalogFamilyTags").mockRejectedValue(
      "tags failed",
    );
    const { result } = renderHook(() => usePlaygroundModelDownload(), {
      wrapper: providerWrapper,
    });

    await waitFor(() => {
      expect(result.current.modelsLoading).toBe(false);
    });

    await act(async () => {
      await result.current.loadFamilyTags("qwen2.5");
    });

    await waitFor(() => {
      expect(result.current.familyTagsError["qwen2.5"]).toBe(
        "Failed to load model tags",
      );
    });
  });

  it("refreshCatalog surfaces non-Error catalog failures", async () => {
    vi.spyOn(adminApi, "fetchPlaygroundModels").mockResolvedValue({ items: [] });
    vi.spyOn(adminApi, "fetchPlaygroundCatalogFamilies").mockRejectedValue(
      "catalog failed",
    );
    const { result } = renderHook(() => usePlaygroundModelDownload(), {
      wrapper: providerWrapper,
    });

    await waitFor(() => {
      expect(result.current.modelsLoading).toBe(false);
    });

    await act(async () => {
      await result.current.refreshCatalog();
    });

    await waitFor(() => {
      expect(result.current.catalogError).toBe("Failed to load playground catalog");
    });
  });

  it("skips poll iteration after download poll is cleared mid-flight", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let resolveList:
      | ((value: { items: { model_id: string; available: boolean }[] }) => void)
      | undefined;
    const listPromise = new Promise<{
      items: { model_id: string; available: boolean }[];
    }>((resolve) => {
      resolveList = resolve;
    });
    vi.spyOn(adminApi, "fetchPlaygroundModels")
      .mockResolvedValueOnce({
        items: [{ model_id: "qwen2.5:3b-instruct", available: false }],
      })
      .mockImplementation(() => listPromise);
    vi.spyOn(adminApi, "pullPlaygroundModel").mockResolvedValue({
      job_id: "00000000-0000-0000-0000-0000000000dd",
      model_id: "qwen2.5:3b-instruct",
      status: "pulling",
    });

    const { result, unmount } = renderHook(() => usePlaygroundModelDownload(), {
      wrapper: providerWrapper,
    });
    await waitFor(() => {
      expect(result.current.modelsLoading).toBe(false);
    });

    await act(async () => {
      await result.current.downloadModel("qwen2.5:3b-instruct");
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(MODEL_PULL_POLL_INTERVAL_MS);
    });

    await act(async () => {
      resolveList?.({
        items: [{ model_id: "qwen2.5:3b-instruct", available: false }],
      });
      unmount();
      await listPromise;
      await vi.advanceTimersByTimeAsync(MODEL_PULL_POLL_INTERVAL_MS);
    });

    vi.useRealTimers();
  });

  it("refreshModels surfaces non-Error list failures", async () => {
    vi.spyOn(adminApi, "fetchPlaygroundModels").mockRejectedValue("list failed");
    const { result } = renderHook(() => usePlaygroundModelDownload(), {
      wrapper: providerWrapper,
    });

    await act(async () => {
      await result.current.refreshModels();
    });

    await waitFor(() => {
      expect(result.current.modelsError).toBe("Failed to load models");
    });
  });

  it("downloadModel ignores whitespace-only tags", async () => {
    vi.spyOn(adminApi, "fetchPlaygroundModels").mockResolvedValue({ items: [] });
    const pullSpy = vi.spyOn(adminApi, "pullPlaygroundModel");
    const { result } = renderHook(() => usePlaygroundModelDownload(), {
      wrapper: providerWrapper,
    });

    await waitFor(() => {
      expect(result.current.modelsLoading).toBe(false);
    });

    await act(async () => {
      await result.current.downloadModel("   ");
    });

    expect(pullSpy).not.toHaveBeenCalled();
    expect(result.current.downloadStatus).toBe("idle");
  });

  it("clears download poll timer when provider unmounts", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.spyOn(adminApi, "fetchPlaygroundModels").mockResolvedValue({
      items: [{ model_id: "qwen2.5:3b-instruct", available: false }],
    });
    vi.spyOn(adminApi, "pullPlaygroundModel").mockResolvedValue({
      job_id: "00000000-0000-0000-0000-0000000000dd",
      model_id: "qwen2.5:3b-instruct",
      status: "pulling",
    });
    const clearTimeoutSpy = vi.spyOn(globalThis, "clearTimeout");

    const { result, unmount } = renderHook(() => usePlaygroundModelDownload(), {
      wrapper: providerWrapper,
    });
    await waitFor(() => {
      expect(result.current.modelsLoading).toBe(false);
    });

    await act(async () => {
      await result.current.downloadModel("qwen2.5:3b-instruct");
    });

    unmount();
    expect(clearTimeoutSpy).toHaveBeenCalled();
    clearTimeoutSpy.mockRestore();
    vi.useRealTimers();
  });
});
