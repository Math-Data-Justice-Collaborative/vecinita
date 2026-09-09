import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { renderWithProviders } from "@/test/renderWithProviders";

import { EnvironmentBanner } from "./EnvironmentBanner";

describe("EnvironmentBanner (UX-1 / F83)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders staging banner when hostname includes staging", () => {
    renderWithProviders(
      <EnvironmentBanner hostname="vecinita-staging-admin-fe.ondigitalocean.app" />,
    );
    const banner = screen.getByTestId("environment-banner");
    expect(banner).toBeInTheDocument();
    expect(banner).toHaveAttribute("data-env", "staging");
    expect(banner).toHaveTextContent(/staging/i);
  });

  it("renders local banner for localhost", () => {
    renderWithProviders(<EnvironmentBanner hostname="localhost" />);
    expect(screen.getByTestId("environment-banner")).toHaveAttribute(
      "data-env",
      "local",
    );
  });

  it("hides banner on production hostnames", () => {
    renderWithProviders(
      <EnvironmentBanner hostname="vecinita-admin-fe.ondigitalocean.app" />,
    );
    expect(screen.queryByTestId("environment-banner")).not.toBeInTheDocument();
  });

  it("honors explicit deployEnvVar over hostname", () => {
    renderWithProviders(
      <EnvironmentBanner hostname="localhost" deployEnvVar="production" />,
    );
    expect(screen.queryByTestId("environment-banner")).not.toBeInTheDocument();
  });
});
