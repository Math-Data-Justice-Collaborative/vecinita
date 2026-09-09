import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { renderWithLocale } from "../test/renderWithLocale";
import { EnvironmentBanner } from "./EnvironmentBanner";

describe("EnvironmentBanner chat (UX-1)", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows staging banner on staging hostname", () => {
    renderWithLocale(
      <EnvironmentBanner
        locale="en"
        hostname="vecinita-staging-chat-fe.ondigitalocean.app"
      />,
    );
    expect(screen.getByTestId("environment-banner")).toHaveAttribute(
      "data-env",
      "staging",
    );
  });
});
