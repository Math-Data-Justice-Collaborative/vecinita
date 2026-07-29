import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TruncatedText } from "@/components/TruncatedText";

const LONG =
  "A very long document title that should be visually truncated in the corpus table layout for operators scanning many rows without horizontal overflow issues";

describe("TruncatedText", () => {
  afterEach(() => {
    cleanup();
  });

  it("exposes full text via title and aria-label without writing cookies", () => {
    const cookieBefore = document.cookie;
    const keysBefore = Object.keys(localStorage);

    render(<TruncatedText text={LONG} data-testid="truncated" />);

    const el = screen.getByTestId("truncated");
    expect(el).toHaveAttribute("title", LONG);
    expect(el).toHaveAttribute("aria-label", LONG);
    expect(el).toHaveClass("truncate");
    expect(el).toHaveTextContent(LONG);
    expect(document.cookie).toBe(cookieBefore);
    expect(Object.keys(localStorage)).toEqual(keysBefore);
  });

  it("renders truncated link with full href and accessible name", () => {
    const url =
      "https://example.com/resources/community/housing/assistance-programs/very-long-path-segment";
    render(
      <TruncatedText as="a" href={url} text={url} data-testid="url-link" />,
    );

    const link = screen.getByTestId("url-link");
    expect(link.tagName).toBe("A");
    expect(link).toHaveAttribute("href", url);
    expect(link).toHaveAttribute("title", url);
    expect(link).toHaveAttribute("aria-label", url);
    expect(link).toHaveClass("truncate");
  });
});
