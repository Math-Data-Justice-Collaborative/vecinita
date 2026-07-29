import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { BoundedTagList } from "@/components/BoundedTagList";

const TAGS = Array.from({ length: 6 }, (_, i) => ({
  slug: `t-${String(i)}`,
  label: `Label ${String(i)}`,
  source: "human" as const,
}));

describe("BoundedTagList", () => {
  afterEach(() => {
    cleanup();
  });

  it("exposes overflow labels via title and aria-label on +N", () => {
    render(<BoundedTagList tags={TAGS} maxVisible={3} moreTestId="more" />);

    const more = screen.getByTestId("more");
    expect(more).toHaveTextContent("+3");
    const overflowLabels = "Label 3, Label 4, Label 5";
    expect(more).toHaveAttribute("title", overflowLabels);
    expect(more).toHaveAttribute("aria-label", overflowLabels);
  });
});
