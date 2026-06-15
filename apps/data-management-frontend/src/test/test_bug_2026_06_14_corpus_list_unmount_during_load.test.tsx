import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { ThemeProvider } from "@/components/ThemeProvider";
import App from "../App";

function renderApp(initialRoute = "/dashboard") {
  return renderWithProviders(
    <ThemeProvider>
      <MemoryRouter initialEntries={[initialRoute]}>
        <App />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("BUG-2026-06-14 corpus list unmount during load", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("does not set state after CorpusList unmounts while fetch is pending", async () => {
    const unhandled: unknown[] = [];
    const onRejection = (reason: unknown) => {
      unhandled.push(reason);
    };
    process.on("unhandledRejection", onRejection);

    let resolveFetch: (value: Response) => void = () => undefined;
    const pendingFetch = new Promise<Response>((resolve) => {
      resolveFetch = resolve;
    });

    vi.stubGlobal("fetch", vi.fn().mockReturnValue(pendingFetch));

    try {
      const { unmount } = renderApp();
      fireEvent.click(screen.getByRole("link", { name: /corpus/i }));
      expect(
        screen.getByText(/ingest urls and manage documents/i),
      ).toBeInTheDocument();

      unmount();

      resolveFetch({
        ok: true,
        json: async () => [],
      } as Response);

      await new Promise((resolve) => {
        setTimeout(resolve, 50);
      });

      expect(unhandled).toEqual([]);
    } finally {
      process.off("unhandledRejection", onRejection);
    }
  });
});
