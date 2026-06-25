import {
  cleanup,
  fireEvent,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { renderWithProviders } from "./renderWithProviders";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ReactElement } from "react";

import { ThemeProvider } from "@/components/ThemeProvider";
import { BulkDeleteDialog } from "@/components/BulkDeleteDialog";
import { BulkMetadataDialog } from "@/components/BulkMetadataDialog";
import { BulkTagDialog } from "@/components/BulkTagDialog";

function renderWithTheme(ui: ReactElement) {
  return renderWithProviders(<ThemeProvider>{ui}</ThemeProvider>);
}

describe("Bulk dialog components", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  describe("BulkTagDialog", () => {
    it("applies tags and closes on full success", async () => {
      const onComplete = vi.fn();
      const onOpenChange = vi.fn();
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({ successes: ["d1"], failures: [] }),
        }),
      );

      renderWithTheme(
        <BulkTagDialog
          open
          onOpenChange={onOpenChange}
          documentIds={["d1"]}
          onComplete={onComplete}
        />,
      );

      fireEvent.change(screen.getByLabelText(/add tags/i), {
        target: { value: "housing, legal" },
      });
      fireEvent.change(screen.getByLabelText(/remove tags/i), {
        target: { value: "old" },
      });
      fireEvent.click(screen.getByRole("button", { name: /apply tags/i }));

      await waitFor(() => {
        expect(onComplete).toHaveBeenCalled();
        expect(onOpenChange).toHaveBeenCalledWith(false);
      });
    });

    it("shows partial failure and keeps dialog open", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            successes: ["d1"],
            failures: [{ document_id: "d2", error: "locked" }],
          }),
        }),
      );

      renderWithTheme(
        <BulkTagDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1", "d2"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /apply tags/i }));

      await waitFor(() => {
        expect(screen.getByText(/1 updated, 1 failed/i)).toBeInTheDocument();
      });
    });

    it("shows API error", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({ ok: false, status: 500 }),
      );

      renderWithTheme(
        <BulkTagDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /apply tags/i }));

      await waitFor(() => {
        expect(screen.getByText(/bulk tag failed/i)).toBeInTheDocument();
      });
    });

    it("uses singular copy for one document", () => {
      renderWithTheme(
        <BulkTagDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={vi.fn()}
        />,
      );
      expect(screen.getByText(/1 document\(s\)\./i)).toBeInTheDocument();
    });

    it("calls onComplete when closing after partial success", async () => {
      const onComplete = vi.fn();
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            successes: ["d1"],
            failures: [{ document_id: "d2", error: "locked" }],
          }),
        }),
      );

      renderWithTheme(
        <BulkTagDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1", "d2"]}
          onComplete={onComplete}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /apply tags/i }));

      await waitFor(() => {
        expect(screen.getByText(/1 updated, 1 failed/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onComplete).toHaveBeenCalled();
    });

    it("shows busy label while applying tags", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation(
          () =>
            new Promise((resolve) => {
              setTimeout(
                () =>
                  resolve({
                    ok: true,
                    json: async () => ({ successes: ["d1"], failures: [] }),
                  }),
                50,
              );
            }),
        ),
      );

      renderWithTheme(
        <BulkTagDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /apply tags/i }));
      expect(screen.getByRole("button", { name: /applying/i })).toBeDisabled();
    });

    it("shows generic tag error for non-Error failures", async () => {
      vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce("tag boom"));

      renderWithTheme(
        <BulkTagDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /apply tags/i }));

      await waitFor(() => {
        expect(screen.getByText(/bulk tag failed/i)).toBeInTheDocument();
      });
    });

    it("does not call onComplete when canceling without results", () => {
      const onComplete = vi.fn();

      renderWithTheme(
        <BulkTagDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={onComplete}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onComplete).not.toHaveBeenCalled();
    });
  });

  describe("BulkMetadataDialog", () => {
    it("updates metadata when fields are provided", async () => {
      const onComplete = vi.fn();
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({ successes: ["d1"], failures: [] }),
        }),
      );

      renderWithTheme(
        <BulkMetadataDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={onComplete}
        />,
      );

      fireEvent.change(screen.getByLabelText(/^title$/i), {
        target: { value: "New title" },
      });
      fireEvent.change(screen.getByLabelText(/^language$/i), {
        target: { value: "es" },
      });
      fireEvent.click(screen.getByRole("button", { name: /update metadata/i }));

      await waitFor(() => {
        expect(onComplete).toHaveBeenCalled();
      });
    });

    it("shows partial failures", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            successes: [],
            failures: [{ document_id: "d1", error: "bad" }],
          }),
        }),
      );

      renderWithTheme(
        <BulkMetadataDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /update metadata/i }));

      await waitFor(() => {
        expect(screen.getByText(/0 updated, 1 failed/i)).toBeInTheDocument();
      });
    });

    it("shows API error", async () => {
      vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce("boom"));

      renderWithTheme(
        <BulkMetadataDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /update metadata/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/bulk metadata update failed/i),
        ).toBeInTheDocument();
      });
    });

    it("calls onComplete when closing after partial success", async () => {
      const onComplete = vi.fn();
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            successes: ["d1"],
            failures: [{ document_id: "d2", error: "bad" }],
          }),
        }),
      );

      renderWithTheme(
        <BulkMetadataDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1", "d2"]}
          onComplete={onComplete}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /update metadata/i }));

      await waitFor(() => {
        expect(screen.getByText(/1 updated, 1 failed/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onComplete).toHaveBeenCalled();
    });

    it("uses plural copy for multiple documents", () => {
      renderWithTheme(
        <BulkMetadataDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1", "d2"]}
          onComplete={vi.fn()}
        />,
      );
      expect(screen.getByText(/2 document\(s\)\./i)).toBeInTheDocument();
    });

    it("shows busy label while updating metadata", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockImplementation(
          () =>
            new Promise((resolve) => {
              setTimeout(
                () =>
                  resolve({
                    ok: true,
                    json: async () => ({ successes: ["d1"], failures: [] }),
                  }),
                50,
              );
            }),
        ),
      );

      renderWithTheme(
        <BulkMetadataDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /update metadata/i }));
      expect(screen.getByRole("button", { name: /updating/i })).toBeDisabled();
    });
  });

  describe("BulkDeleteDialog", () => {
    it("deletes documents on confirm", async () => {
      const onComplete = vi.fn();
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({ successes: ["d1"], failures: [] }),
        }),
      );

      renderWithTheme(
        <BulkDeleteDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={onComplete}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));

      await waitFor(() => {
        expect(onComplete).toHaveBeenCalled();
      });
    });

    it("lists partial delete failures", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            successes: ["d1"],
            failures: [{ document_id: "d2", error: "not found" }],
          }),
        }),
      );

      renderWithTheme(
        <BulkDeleteDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1", "d2"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));

      await waitFor(() => {
        expect(screen.getByText(/d2: not found/i)).toBeInTheDocument();
      });
    });

    it("shows API error", async () => {
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({ ok: false, status: 500 }),
      );

      renderWithTheme(
        <BulkDeleteDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));

      await waitFor(() => {
        expect(screen.getByText(/bulk delete failed/i)).toBeInTheDocument();
      });
    });

    it("calls onComplete on close after partial success", async () => {
      const onComplete = vi.fn();
      vi.stubGlobal(
        "fetch",
        vi.fn().mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            successes: ["d1"],
            failures: [{ document_id: "d2", error: "x" }],
          }),
        }),
      );

      renderWithTheme(
        <BulkDeleteDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1", "d2"]}
          onComplete={onComplete}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));

      await waitFor(() => {
        expect(screen.getByText(/d2: x/i)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onComplete).toHaveBeenCalled();
    });

    it("uses plural copy for multiple documents", () => {
      renderWithTheme(
        <BulkDeleteDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1", "d2"]}
          onComplete={vi.fn()}
        />,
      );
      const dialog = screen.getByRole("dialog");
      expect(within(dialog).getByText(/2 document\(s\)/i)).toBeInTheDocument();
    });

    it("shows generic delete error for non-Error failures", async () => {
      vi.stubGlobal("fetch", vi.fn().mockRejectedValueOnce("delete boom"));

      renderWithTheme(
        <BulkDeleteDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={vi.fn()}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /confirm delete/i }));

      await waitFor(() => {
        expect(screen.getByText(/bulk delete failed/i)).toBeInTheDocument();
      });
    });

    it("does not call onComplete when canceling without results", () => {
      const onComplete = vi.fn();

      renderWithTheme(
        <BulkDeleteDialog
          open
          onOpenChange={vi.fn()}
          documentIds={["d1"]}
          onComplete={onComplete}
        />,
      );

      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onComplete).not.toHaveBeenCalled();
    });
  });
});
