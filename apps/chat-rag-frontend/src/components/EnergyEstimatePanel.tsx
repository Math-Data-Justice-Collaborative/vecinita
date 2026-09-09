import { useState } from "react";

import type { EnergyEstimate } from "../api/types";
import type { Locale } from "../hooks/useLocale.types";
import { t } from "vecinita-frontend-i18n";

const KM_TO_MI = 0.621371;

type EnergyEstimatePanelProps = {
  estimate: EnergyEstimate;
  locale: Locale;
};

function formatMeters(meters: number): string {
  if (meters >= 1000) {
    return meters.toFixed(0);
  }
  if (meters >= 1) {
    return meters.toFixed(1);
  }
  return meters.toFixed(2);
}

function formatMiles(km: number): string {
  const miles = km * KM_TO_MI;
  if (miles >= 1) {
    return miles.toFixed(2);
  }
  if (miles >= 0.01) {
    return miles.toFixed(3);
  }
  return miles.toFixed(4);
}

/**
 * Post-ask energy chip; car/advisory/guide collapsed by default (F65 / UJ-070 / UX-2).
 */
export function EnergyEstimatePanel({
  estimate,
  locale,
}: EnergyEstimatePanelProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [guideOpen, setGuideOpen] = useState(false);
  const meters = formatMeters(estimate.car_m_equiv);
  const miles = formatMiles(estimate.car_km_equiv);
  const wh =
    estimate.wh < 0.01 ? estimate.wh.toFixed(4) : estimate.wh.toFixed(2);
  const gCo2e =
    estimate.g_co2e < 0.01
      ? estimate.g_co2e.toFixed(4)
      : estimate.g_co2e.toFixed(2);

  return (
    <aside
      className="energy-estimate"
      data-testid="energy-estimate"
      aria-label={t(locale, "chat.energyEstimateLabel")}
    >
      <div className="energy-estimate-summary">
        <p className="energy-chip" data-testid="energy-chip">
          {t(locale, "chat.energyEstimateLabel")}: {wh} Wh · {gCo2e} gCO2e
        </p>
        <button
          type="button"
          className="energy-details-toggle secondary"
          data-testid="energy-details-toggle"
          aria-expanded={detailsOpen}
          onClick={() => {
            setDetailsOpen((open) => !open);
          }}
        >
          {detailsOpen
            ? t(locale, "chat.energyDetailsHide")
            : t(locale, "chat.energyDetailsShow")}
        </button>
      </div>
      {detailsOpen ? (
        <div className="energy-estimate-details" data-testid="energy-details">
          <p className="energy-car-line" data-testid="energy-car-line">
            {t(locale, "chat.energyCarPrefix")} {meters} m (≈ {miles} mi){" "}
            {t(locale, "chat.energyCarSuffix")}
          </p>
          <p
            className="energy-advisory"
            data-testid="energy-advisory"
            role="note"
          >
            {t(locale, "chat.energyAdvisory")}
          </p>
          <button
            type="button"
            className="energy-use-guide-toggle secondary"
            data-testid="energy-use-guide-toggle"
            aria-expanded={guideOpen}
            onClick={() => {
              setGuideOpen((open) => !open);
            }}
          >
            {t(locale, "chat.energyUseGuideToggle")}
          </button>
          {guideOpen ? (
            <div className="energy-use-guide" data-testid="energy-use-guide">
              <p>{t(locale, "chat.energyUseGuideBody")}</p>
            </div>
          ) : null}
        </div>
      ) : null}
    </aside>
  );
}
