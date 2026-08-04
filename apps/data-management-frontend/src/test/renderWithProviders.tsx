import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { LocaleProvider, TooltipProvider } from "vecinita-frontend-ui";

import { AuthProvider } from "@/auth/AuthContext";
import { ThemeProvider } from "@/components/ThemeProvider";

function AllProviders({ children }: { children: ReactNode }) {
  return (
    <LocaleProvider>
      <TooltipProvider delayDuration={0}>
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </TooltipProvider>
    </LocaleProvider>
  );
}

export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">,
) {
  return render(ui, { wrapper: AllProviders, ...options });
}
