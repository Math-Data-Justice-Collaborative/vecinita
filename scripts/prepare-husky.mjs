#!/usr/bin/env node
/** Skip husky when disabled or unavailable (DO App Platform / CI npm ci). */
if (process.env.HUSKY === "0") {
  process.exit(0);
}

import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

try {
  const huskyBin = require.resolve("husky/bin.mjs");
  execFileSync(process.execPath, [huskyBin], { stdio: "inherit" });
} catch {
  process.exit(0);
}
