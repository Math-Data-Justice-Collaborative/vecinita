import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { Source } from "../api/types";
import { SourceList } from "./SourceList";

const SOURCE: Source = {
  chunk_id: "c1",
  document_id: "d1",
  title: "Food pantry",
  url: "https://example.com/pantry",
  score: 0.9123,
};

describe("SourceList", () => {
  afterEach(() => {
    cleanup();
  });

  it("returns null when sources array is empty", () => {
    const { container } = render(<SourceList sources={[]} locale="en" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders linked sources with score", () => {
    render(<SourceList sources={[SOURCE]} locale="en" />);
    const link = screen.getByRole("link", { name: /food pantry/i });
    expect(link).toHaveAttribute("href", "https://example.com/pantry");
    expect(screen.getByText("(0.91)")).toBeInTheDocument();
  });

  it("uses the URL as link text when title is missing", () => {
    const urlOnly: Source = {
      chunk_id: "c3",
      document_id: "d3",
      title: null,
      url: "https://example.com/raw",
      score: 0.4,
    };
    render(<SourceList sources={[urlOnly]} locale="en" />);
    expect(
      screen.getByRole("link", { name: "https://example.com/raw" }),
    ).toBeInTheDocument();
  });

  it("renders plain title when url is missing", () => {
    const noUrl: Source = {
      chunk_id: "c1",
      document_id: "d1",
      title: "Food pantry",
      score: 0.9123,
    };
    const { container } = render(<SourceList sources={[noUrl]} locale="en" />);
    expect(container.querySelector("a")).toBeNull();
    expect(screen.getByText("Food pantry")).toBeInTheDocument();
  });

  it("falls back to corpus chunk label when title and url are missing", () => {
    const bare: Source = {
      chunk_id: "c2",
      document_id: "d2",
      title: null,
      url: "",
      score: 0.5,
    };
    render(<SourceList sources={[bare]} locale="es" />);
    expect(screen.getByText("Fragmento del corpus")).toBeInTheDocument();
  });
});
