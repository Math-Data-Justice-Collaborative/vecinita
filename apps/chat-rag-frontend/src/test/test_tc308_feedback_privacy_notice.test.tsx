import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FeedbackPage } from "../components/FeedbackPage";

describe("TC-308 Feedback privacy notice (F68 / #214)", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows expanded EN privacy callout and intro above the form", () => {
    render(<FeedbackPage locale="en" onNavigateHome={() => undefined} />);
    const notice = screen.getByTestId("feedback-privacy-notice");
    expect(notice).toBeInTheDocument();
    expect(notice.textContent ?? "").toMatch(/email/i);
    expect(notice.textContent ?? "").toMatch(
      /medical|immigration|SSN|phone|address/i,
    );
    expect(screen.getByTestId("feedback-intro")).toBeInTheDocument();
    const form = screen.getByTestId("feedback-form");
    expect(
      notice.compareDocumentPosition(form) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("shows expanded ES privacy callout and intro above the form", () => {
    render(<FeedbackPage locale="es" onNavigateHome={() => undefined} />);
    const notice = screen.getByTestId("feedback-privacy-notice");
    expect(notice).toBeInTheDocument();
    expect(notice.textContent ?? "").toMatch(/correo|email/i);
    expect(notice.textContent ?? "").toMatch(
      /médic|migraci|SSN|teléfono|dirección|sensible/i,
    );
    expect(screen.getByTestId("feedback-intro")).toBeInTheDocument();
  });
});
