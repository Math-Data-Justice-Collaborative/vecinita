import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders default button", () => {
    render(<Button>Click</Button>);
    expect(screen.getByRole("button", { name: "Click" })).toBeInTheDocument();
  });

  it("renders variant and size combinations", () => {
    render(
      <>
        <Button variant="destructive">Del</Button>
        <Button variant="outline">Out</Button>
        <Button variant="secondary">Sec</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="link">Link</Button>
        <Button size="sm">Sm</Button>
        <Button size="lg">Lg</Button>
        <Button size="icon" aria-label="icon" />
      </>,
    );
    expect(screen.getByRole("button", { name: "Del" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "icon" })).toBeInTheDocument();
  });

  it("renders as child slot when asChild is true", () => {
    render(
      <Button asChild>
        <a href="https://example.com">Anchor</a>
      </Button>,
    );
    expect(screen.getByRole("link", { name: "Anchor" })).toBeInTheDocument();
  });
});
