import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { renderWithProviders } from "@/test/renderWithProviders";

import { PageLoadingState } from "./PageLoadingState";

describe("PageLoadingState (UX-3)", () => {
  afterEach(() => {
    cleanup();
  });

  it("exposes busy status with skeleton placeholders", () => {
    renderWithProviders(<PageLoadingState />);
    const root = screen.getByTestId("page-loading");
    expect(root).toHaveAttribute("aria-busy", "true");
    expect(root).toHaveAttribute("role", "status");
    expect(screen.getByTestId("page-loading-skeletons")).toBeInTheDocument();
  });

  it("shows slow-load message and retry when timedOut", () => {
    const onRetry = () => undefined;
    renderWithProviders(<PageLoadingState timedOut onRetry={onRetry} />);
    expect(screen.getByTestId("page-loading-slow")).toBeInTheDocument();
    expect(screen.getByTestId("page-loading-retry")).toBeInTheDocument();
  });
});
