import { afterEach, describe, expect, it, vi } from "vitest";

import {
  LOCALE_STORAGE_KEY,
  detectBrowserLocale,
  readStoredLocale,
} from "../locale";

describe("detectBrowserLocale", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns es when the browser language starts with es", () => {
    vi.spyOn(navigator, "language", "get").mockReturnValue("es-MX");
    expect(detectBrowserLocale()).toBe("es");
  });

  it("returns en when the browser language starts with en", () => {
    vi.spyOn(navigator, "language", "get").mockReturnValue("en-US");
    expect(detectBrowserLocale()).toBe("en");
  });

  it("falls back to es for any other browser language", () => {
    vi.spyOn(navigator, "language", "get").mockReturnValue("fr-FR");
    expect(detectBrowserLocale()).toBe("es");
  });
});

describe("readStoredLocale", () => {
  afterEach(() => {
    localStorage.clear();
  });

  it("returns the stored locale when it is en", () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "en");
    expect(readStoredLocale()).toBe("en");
  });

  it("returns the stored locale when it is es", () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "es");
    expect(readStoredLocale()).toBe("es");
  });

  it("returns null when nothing is stored", () => {
    expect(readStoredLocale()).toBeNull();
  });

  it("returns null when the stored value is not a supported locale", () => {
    localStorage.setItem(LOCALE_STORAGE_KEY, "de");
    expect(readStoredLocale()).toBeNull();
  });
});
