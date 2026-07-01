/** Suppress expected Vitest/jsdom stderr from intentional negative hook-boundary tests. */
export function filterExpectedVitestConsoleLog(
  log: string,
  type: "stdout" | "stderr",
): boolean | undefined {
  if (type !== "stderr") {
    return undefined;
  }
  if (/must be used within/i.test(log)) {
    return false;
  }
  if (/Multiple GoTrueClient instances detected/i.test(log)) {
    return false;
  }
  // React 18 logs a dev stack trace before the hook guard throws (expected in negative tests).
  if (
    /react-dom\/cjs\/react-dom\.development\.js/.test(log) ||
    /@testing-library\/react\/dist\/pure\.js/.test(log) ||
    /HTMLUnknownElement\.callCallback/.test(log) ||
    /invokeEventListeners/.test(log)
  ) {
    return false;
  }
  return undefined;
}
