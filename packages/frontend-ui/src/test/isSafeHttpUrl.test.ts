import { describe, expect, it } from "vitest";

import { citationHref, isSafeHttpUrl } from "../isSafeHttpUrl";

describe("isSafeHttpUrl / citationHref (TC-242–244 / F72)", () => {
  it("accepts absolute https URLs (TC-242)", () => {
    expect(isSafeHttpUrl("https://example.org/page")).toBe(true);
    expect(citationHref("https://example.org/page")).toBe(
      "https://example.org/page",
    );
  });

  it("accepts absolute http URLs (TC-242)", () => {
    expect(isSafeHttpUrl("http://example.org/page")).toBe(true);
    expect(citationHref("http://example.org/page")).toBe(
      "http://example.org/page",
    );
  });

  it("rejects relative paths (TC-243)", () => {
    expect(isSafeHttpUrl("/relative/path")).toBe(false);
    expect(isSafeHttpUrl("relative/path")).toBe(false);
    expect(citationHref("/relative/path")).toBeNull();
  });

  it("rejects fixture and javascript schemes (TC-243)", () => {
    expect(isSafeHttpUrl("fixture://corpus/doc-1")).toBe(false);
    expect(isSafeHttpUrl("javascript:alert(1)")).toBe(false);
    expect(citationHref("fixture://corpus/doc-1")).toBeNull();
    expect(citationHref("javascript:alert(1)")).toBeNull();
  });

  it("rejects empty and whitespace-only URLs (TC-243)", () => {
    expect(isSafeHttpUrl("")).toBe(false);
    expect(isSafeHttpUrl("   ")).toBe(false);
    expect(citationHref("")).toBeNull();
    expect(citationHref("   ")).toBeNull();
  });

  it("rejects null and undefined (TC-244)", () => {
    expect(isSafeHttpUrl(null)).toBe(false);
    expect(isSafeHttpUrl(undefined)).toBe(false);
    expect(citationHref(null)).toBeNull();
    expect(citationHref(undefined)).toBeNull();
  });
});
