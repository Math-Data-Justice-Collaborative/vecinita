import { useLayoutEffect, useRef, useState } from "react";

import type { Locale } from "../hooks/useLocale.types";
import { t } from "../i18n/messages";
import { FACT_ROTATION_MS } from "../coldstart/constants";
import { resolveDonateUrl } from "../coldstart/donateUrl";
import { factText, pickNextFact, type ColdStartFact } from "../coldstart/facts";
import {
  getColdStartConsent,
  rememberSeenFactId,
  setColdStartConsent,
  type ColdStartConsent,
} from "../coldstart/prefs";

type ColdStartWaitProps = {
  locale: Locale;
  active: boolean;
};

/**
 * Rotating typed wait catalog (fact | tip | marketing) + soft donate CTA +
 * consent banner during cold-start / long-wait (F40 / F64 / UJ-052 / UJ-069 /
 * ADR-039).
 */
export function ColdStartWait({ locale, active }: ColdStartWaitProps) {
  const [consent, setConsent] = useState<ColdStartConsent>(() =>
    getColdStartConsent(),
  );
  const [fact, setFact] = useState<ColdStartFact | null>(null);
  const nextIndexRef = useRef(0);

  useLayoutEffect(() => {
    if (!active) {
      setFact(null);
      return;
    }

    const preferUnseen = consent === "accept";
    const first = pickNextFact(0, { preferUnseen });
    setFact(first.fact);
    nextIndexRef.current = first.nextIndex;
    if (preferUnseen) {
      rememberSeenFactId(first.fact.id);
    }

    const timer = window.setInterval(() => {
      const prefer = getColdStartConsent() === "accept";
      const picked = pickNextFact(nextIndexRef.current, {
        preferUnseen: prefer,
      });
      nextIndexRef.current = picked.nextIndex;
      setFact(picked.fact);
      if (prefer) {
        rememberSeenFactId(picked.fact.id);
      }
    }, FACT_ROTATION_MS);

    return () => {
      window.clearInterval(timer);
    };
  }, [active, consent]);

  if (!active || !fact) {
    return null;
  }

  const donateHref = resolveDonateUrl();
  const showBanner = consent === null;

  return (
    <div className="cold-start-wait" data-testid="cold-start-wait">
      <p className="status-hint" role="status">
        {t(locale, "coldStartStatus")}
      </p>
      <p
        className="cold-start-fact"
        data-testid="cold-start-fact"
        data-kind={fact.kind}
      >
        {factText(fact, locale)}
      </p>
      <p className="cold-start-donate">
        <a
          href={donateHref}
          target="_blank"
          rel="noopener noreferrer"
          data-testid="cold-start-donate"
        >
          {t(locale, "coldStartDonateCta")}
        </a>
      </p>
      {showBanner ? (
        <div
          className="cold-start-consent"
          data-testid="cold-start-consent"
          role="region"
          aria-label={t(locale, "coldStartConsentLabel")}
        >
          <p className="cold-start-consent-copy">
            {t(locale, "coldStartConsentCopy")}
          </p>
          <div className="cold-start-consent-actions">
            <button
              type="button"
              data-testid="cold-start-consent-accept"
              onClick={() => {
                setColdStartConsent("accept");
                setConsent("accept");
              }}
            >
              {t(locale, "coldStartConsentAccept")}
            </button>
            <button
              type="button"
              className="secondary"
              data-testid="cold-start-consent-opt-out"
              onClick={() => {
                setColdStartConsent("opt_out");
                setConsent("opt_out");
              }}
            >
              {t(locale, "coldStartConsentOptOut")}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
