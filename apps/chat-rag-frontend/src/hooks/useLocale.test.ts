import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { detectBrowserLocale, readStoredLocale, useLocale } from "./useLocale";

describe("useLocale.types helpers", () => {
  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("readStoredLocale returns en or es when valid", () => {
    localStorage.setItem("vecinita.locale", "en");
    expect(readStoredLocale()).toBe("en");
    localStorage.setItem("vecinita.locale", "es");
    expect(readStoredLocale()).toBe("es");
  });

  it("readStoredLocale returns null for invalid stored values", () => {
    localStorage.setItem("vecinita.locale", "fr");
    expect(readStoredLocale()).toBeNull();
  });

  it("detectBrowserLocale maps en and es prefixes", () => {
    vi.stubGlobal("navigator", { language: "en-US" });
    expect(detectBrowserLocale()).toBe("en");
    vi.stubGlobal("navigator", { language: "es-MX" });
    expect(detectBrowserLocale()).toBe("es");
  });
});

describe("useLocale", () => {
  it("throws when used outside LocaleProvider", () => {
    const consoleError = vi
      .spyOn(console, "error")
      .mockImplementation(() => {});
    expect(() => renderHook(() => useLocale())).toThrow(/LocaleProvider/i);
    consoleError.mockRestore();
  });
});
