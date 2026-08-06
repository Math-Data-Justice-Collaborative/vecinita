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

  it("renders linked sources with score (TC-242)", () => {
    render(<SourceList sources={[SOURCE]} locale="en" />);
    const link = screen.getByRole("link", { name: /food pantry/i });
    expect(link).toHaveAttribute("href", "https://example.com/pantry");
    expect(screen.getByText("(0.91)")).toBeInTheDocument();
  });

  it("links absolute http URLs (TC-242)", () => {
    const httpSource: Source = {
      ...SOURCE,
      chunk_id: "c-http",
      url: "http://example.com/pantry",
    };
    render(<SourceList sources={[httpSource]} locale="en" />);
    expect(screen.getByRole("link", { name: /food pantry/i })).toHaveAttribute(
      "href",
      "http://example.com/pantry",
    );
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

  it("renders plain title when url is missing (TC-244)", () => {
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

  it("renders plain title for fixture:// URLs (TC-243)", () => {
    const fixture: Source = {
      chunk_id: "c-fix",
      document_id: "d-fix",
      title: "Fixture doc",
      url: "fixture://corpus/doc-1",
      score: 0.8,
    };
    const { container } = render(<SourceList sources={[fixture]} locale="en" />);
    expect(container.querySelector("a")).toBeNull();
    expect(screen.getByText("Fixture doc")).toBeInTheDocument();
  });

  it("renders plain title for relative and javascript URLs (TC-243)", () => {
    const relative: Source = {
      chunk_id: "c-rel",
      document_id: "d-rel",
      title: "Relative",
      url: "/local/path",
      score: 0.7,
    };
    const js: Source = {
      chunk_id: "c-js",
      document_id: "d-js",
      title: "JS",
      url: "javascript:alert(1)",
      score: 0.6,
    };
    const { container, rerender } = render(
      <SourceList sources={[relative]} locale="en" />,
    );
    expect(container.querySelector("a")).toBeNull();
    expect(screen.getByText("Relative")).toBeInTheDocument();
    rerender(<SourceList sources={[js]} locale="en" />);
    expect(container.querySelector("a")).toBeNull();
    expect(screen.getByText("JS")).toBeInTheDocument();
  });
});
