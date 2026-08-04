import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ChatPanel } from "../components/ChatPanel";
import { renderWithLocale } from "./renderWithLocale";

function sseResponse(body: string): Response {
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(body));
      controller.close();
    },
  });
  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

function mockFetchRouter(handlers: { stream?: Response }) {
  return vi.fn((input: RequestInfo | URL) => {
    const url = typeof input === "string" ? input : input.toString();
    if (url.includes("/api/v1/warm")) {
      return Promise.resolve(
        new Response(JSON.stringify({ status: "warming" }), { status: 200 }),
      );
    }
    if (url.includes("/api/v1/tags")) {
      return Promise.resolve(
        new Response(JSON.stringify({ tags: [] }), { status: 200 }),
      );
    }
    if (url.includes("/api/v1/ask/stream")) {
      if (!handlers.stream) {
        return Promise.reject(new Error("Unexpected ask/stream fetch"));
      }
      return Promise.resolve(handlers.stream);
    }
    return Promise.reject(new Error(`Unexpected fetch: ${url}`));
  });
}

const ENERGY_DONE =
  'data: {"token":"Hours "}\n\n' +
  'data: {"token":"posted."}\n\n' +
  'data: {"sources":[]}\n\n' +
  'data: {"done":true,"cache_hit":"none","energy_estimate":{"wh":0.02,"g_co2e":0.008,"method":"tdp_util_walltime_v1","advisory":"Approximate.","car_km_equiv":0.00003,"car_m_equiv":0.03}}\n\n';

describe("UJ-070 / F65 energy estimate in ChatPanel (TC-220, TC-231)", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("shows energy chip and car line after stream done", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchRouter({
        stream: sseResponse(ENERGY_DONE),
      }),
    );

    renderWithLocale(<ChatPanel />);
    fireEvent.change(screen.getByLabelText(/your question/i), {
      target: { value: "When is the food pantry open?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    await waitFor(() => {
      expect(screen.getByTestId("energy-estimate")).toBeInTheDocument();
    });
    expect(screen.getByTestId("energy-chip")).toHaveTextContent(/Wh/i);
    expect(screen.getByTestId("energy-car-line")).toHaveTextContent(/mi/);
    expect(screen.getByTestId("energy-advisory")).toHaveTextContent(
      /approximate/i,
    );
  });
});
