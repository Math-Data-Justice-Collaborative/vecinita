import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";

// Chat history persists to `sessionStorage` (F33). Clear it between tests so
// one test's conversation never rehydrates into the next.
afterEach(() => {
  sessionStorage.clear();
});
