import { act, renderHook, waitFor } from "@testing-library/react";
import { createElement, type ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import * as adminApi from "@/api/admin";

import {
  OllamaModelDownloadProvider,
  firstAvailableModelId,
  modelOptionLabel,
  useOllamaModelDownload,
} from "./useOllamaModelDownload";

function providerWrapper({ children }: { children: ReactNode }) {
  return createElement(OllamaModelDownloadProvider, null, children);
}

describe("useOllamaModelDownload helpers", () => {
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

describe("useOllamaModelDownload hook", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("refreshModels surfaces non-Error list failures", async () => {
    vi.spyOn(adminApi, "fetchOllamaModels").mockRejectedValue("list failed");
    const { result } = renderHook(() => useOllamaModelDownload(), {
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
    vi.spyOn(adminApi, "fetchOllamaModels").mockResolvedValue({ items: [] });
    const pullSpy = vi.spyOn(adminApi, "pullOllamaModel");
    const { result } = renderHook(() => useOllamaModelDownload(), {
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
    vi.spyOn(adminApi, "fetchOllamaModels").mockResolvedValue({
      items: [{ model_id: "qwen2.5:3b-instruct", available: false }],
    });
    vi.spyOn(adminApi, "pullOllamaModel").mockResolvedValue({
      job_id: "00000000-0000-0000-0000-0000000000dd",
      model_id: "qwen2.5:3b-instruct",
      status: "pulling",
    });
    const clearTimeoutSpy = vi.spyOn(globalThis, "clearTimeout");

    const { result, unmount } = renderHook(() => useOllamaModelDownload(), {
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
