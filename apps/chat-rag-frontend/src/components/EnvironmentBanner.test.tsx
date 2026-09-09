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

  it("shows local banner for localhost", () => {
    renderWithLocale(<EnvironmentBanner locale="en" hostname="localhost" />);
    expect(screen.getByTestId("environment-banner")).toHaveAttribute(
      "data-env",
      "local",
    );
  });

  it("hides banner on production hostnames", () => {
    renderWithLocale(
      <EnvironmentBanner
        locale="en"
        hostname="vecinita-chat-fe.ondigitalocean.app"
      />,
    );
    expect(screen.queryByTestId("environment-banner")).not.toBeInTheDocument();
  });

  it("honors explicit deployEnvVar over hostname", () => {
    renderWithLocale(
      <EnvironmentBanner
        locale="en"
        hostname="localhost"
        deployEnvVar="production"
      />,
    );
    expect(screen.queryByTestId("environment-banner")).not.toBeInTheDocument();
  });
});
