import { render, type RenderResult } from "@testing-library/react";
import type { ReactElement } from "react";

import { LocaleProvider } from "../context/LocaleContext";

export function renderWithLocale(ui: ReactElement): RenderResult {
  return render(<LocaleProvider>{ui}</LocaleProvider>);
}
