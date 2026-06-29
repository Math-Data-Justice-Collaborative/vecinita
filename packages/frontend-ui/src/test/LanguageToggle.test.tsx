import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { LanguageToggle } from "../LanguageToggle";

describe("LanguageToggle", () => {
  afterEach(() => {
    cleanup();
  });

  it("marks EN as pressed when the locale is en", () => {
    render(<LanguageToggle locale="en" onChange={() => undefined} />);

    expect(screen.getByRole("button", { name: "EN" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "ES" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("marks ES as pressed when the locale is es", () => {
    render(<LanguageToggle locale="es" onChange={() => undefined} />);

    expect(screen.getByRole("button", { name: "ES" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "EN" })).toHaveAttribute(
      "aria-pressed",
      "false",
    );
  });

  it("invokes onChange with en when EN is clicked", () => {
    const onChange = vi.fn();
    render(<LanguageToggle locale="es" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "EN" }));
    expect(onChange).toHaveBeenCalledWith("en");
  });

  it("invokes onChange with es when ES is clicked", () => {
    const onChange = vi.fn();
    render(<LanguageToggle locale="en" onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "ES" }));
    expect(onChange).toHaveBeenCalledWith("es");
  });
});
