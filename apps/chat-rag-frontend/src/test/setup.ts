import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";

// Chat history persists to device-local `localStorage` (F33, ADR-025). Clear it
// between tests so one test's conversation never rehydrates into the next.
afterEach(() => {
  localStorage.removeItem("vecinita.chat.history.v1");
  sessionStorage.clear();
});
