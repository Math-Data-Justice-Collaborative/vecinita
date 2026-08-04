import { render, type RenderResult } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";
import { TooltipProvider } from "vecinita-frontend-ui";

import { LocaleProvider } from "../context/LocaleContext";

function Providers({ children }: { children: ReactNode }) {
  return (
    <LocaleProvider>
      <TooltipProvider delayDuration={0}>{children}</TooltipProvider>
    </LocaleProvider>
  );
}

export function renderWithLocale(ui: ReactElement): RenderResult {
  return render(ui, { wrapper: Providers });
}
