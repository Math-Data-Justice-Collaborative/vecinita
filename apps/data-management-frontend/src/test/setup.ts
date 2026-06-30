import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach } from "vitest";

import { setSupabaseClientForTests } from "@/auth/supabaseClient";

import { installAuthenticatedSupabaseMock } from "./supabaseMock";

beforeEach(() => {
  installAuthenticatedSupabaseMock();
});

afterEach(() => {
  setSupabaseClientForTests(null);
});

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: query.includes("min-width: 768px"),
    media: query,
    onchange: null,
    addListener: () => undefined,
    removeListener: () => undefined,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  }),
});

class ResizeObserverStub {
  observe(): void {
    return undefined;
  }
  unobserve(): void {
    return undefined;
  }
  disconnect(): void {
    return undefined;
  }
}

Object.defineProperty(globalThis, "ResizeObserver", {
  writable: true,
  value: ResizeObserverStub,
});
