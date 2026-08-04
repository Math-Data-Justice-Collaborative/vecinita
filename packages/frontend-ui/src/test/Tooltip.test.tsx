import "@testing-library/jest-dom/vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { Tooltip, TooltipProvider } from "../Tooltip";

describe("Tooltip (TC-223, TC-224 / F67)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders English tooltip content when open (TC-223)", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <Tooltip content="Toggle theme" open>
          <button type="button">theme</button>
        </Tooltip>
      </TooltipProvider>,
    );
    expect(screen.getByRole("tooltip")).toHaveTextContent("Toggle theme");
  });

  it("renders Spanish tooltip content when open (TC-223)", () => {
    render(
      <TooltipProvider delayDuration={0}>
        <Tooltip content="Cambiar tema" open>
          <button type="button">tema</button>
        </Tooltip>
      </TooltipProvider>,
    );
    expect(screen.getByRole("tooltip")).toHaveTextContent("Cambiar tema");
  });

  it("shows tooltip on keyboard focus without hover (TC-224)", async () => {
    render(
      <TooltipProvider delayDuration={0}>
        <Tooltip content="Language">
          <button type="button">lang</button>
        </Tooltip>
      </TooltipProvider>,
    );

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();

    const trigger = screen.getByRole("button", { name: "lang" });
    trigger.focus();
    fireEvent.focus(trigger);

    await waitFor(() => {
      expect(screen.getByRole("tooltip")).toHaveTextContent("Language");
    });
  });
});
