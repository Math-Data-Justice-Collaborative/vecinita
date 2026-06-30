import "@testing-library/jest-dom/vitest";
import type { ComponentProps } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LocaleProvider } from "../LocaleProvider";
import { PaginationControls } from "../PaginationControls";

function renderControls(
  props: Partial<React.ComponentProps<typeof PaginationControls>> = {},
) {
  const onPrevious = vi.fn();
  const onNext = vi.fn();
  render(
    <LocaleProvider>
      <PaginationControls
        page={2}
        totalPages={5}
        total={42}
        onPrevious={onPrevious}
        onNext={onNext}
        {...props}
      />
    </LocaleProvider>,
  );
  return { onPrevious, onNext };
}

describe("PaginationControls (TC-068)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders page summary and navigation buttons", () => {
    renderControls();
    expect(screen.getByTestId("pagination-controls")).toBeInTheDocument();
    expect(screen.getByText(/page 2 of 5/i)).toBeInTheDocument();
    expect(screen.getByTestId("pagination-previous")).toBeInTheDocument();
    expect(screen.getByTestId("pagination-next")).toBeInTheDocument();
  });

  it("calls onPrevious and onNext when buttons are clicked", () => {
    const { onPrevious, onNext } = renderControls();
    fireEvent.click(screen.getByTestId("pagination-previous"));
    fireEvent.click(screen.getByTestId("pagination-next"));
    expect(onPrevious).toHaveBeenCalledTimes(1);
    expect(onNext).toHaveBeenCalledTimes(1);
  });

  it("disables buttons when requested", () => {
    renderControls({ previousDisabled: true, nextDisabled: true });
    expect(screen.getByTestId("pagination-previous")).toBeDisabled();
    expect(screen.getByTestId("pagination-next")).toBeDisabled();
  });
});
