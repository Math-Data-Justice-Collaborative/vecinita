/** Initial chat sidebar open state from viewport width (drawer breakpoint 768). */

export const SIDEBAR_DRAWER_MAX_WIDTH_PX = 768;

/** Desktop (≥769): open. Phone/tablet drawer (≤768): closed. */
export function initialSidebarOpen(viewportWidthPx: number): boolean {
  return viewportWidthPx > SIDEBAR_DRAWER_MAX_WIDTH_PX;
}
