/**
 * TC-067 compile-time guard: unknown dot-path keys must fail typecheck.
 * Verified via `npm run typecheck` once MessageKey typing lands in T33.2.
 */
import { t } from "../t";

function assertInvalidKeyRejected(): void {
  // @ts-expect-error unknown message key must not compile
  t("en", "shared.doesNotExist");
}

assertInvalidKeyRejected();
