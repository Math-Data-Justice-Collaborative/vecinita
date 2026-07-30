import type { Locale } from "../hooks/useLocale.types";
import { getSeenFactIds } from "./prefs";

/** Curated from Phase 0 WRWC / Providence scrape pool (~10). */
export type ColdStartFact = {
  id: string;
  en: string;
  es: string;
};

export const COLD_START_FACTS: readonly ColdStartFact[] = [
  {
    id: "heritage-river",
    en: "The Woonasquatucket is one of only 14 American Heritage Rivers in the U.S.",
    es: "El Woonasquatucket es uno de solo 14 ríos American Heritage en EE. UU.",
  },
  {
    id: "algonquian-name",
    en: "“Woonasquatucket” is Algonquian — roughly “where the salt water ends.”",
    es: "“Woonasquatucket” es algonquino — aproximadamente “donde termina el agua salada.”",
  },
  {
    id: "wrwc-towns",
    en: "WRWC restores the river, Greenway, and nearby communities across about six RI towns.",
    es: "WRWC restaura el río, el Greenway y comunidades cercanas en unas seis ciudades de RI.",
  },
  {
    id: "river-hero",
    en: "You can become a “River Hero” — gifts fund paths, parks, and cleaner water.",
    es: "Puedes ser un “River Hero” — las donaciones financian senderos, parques y agua más limpia.",
  },
  {
    id: "ways-to-give",
    en: "Ways to give include monthly gifts, stock, employer match, IRA QCD, and Fish Dedications at parks.",
    es: "Formas de donar: regalos mensuales, acciones, contrapartida del empleador, IRA QCD y dedicaciones de peces en parques.",
  },
  {
    id: "what-cheer",
    en: "Providence’s motto is “What Cheer?” — from a Narragansett greeting to Roger Williams.",
    es: "El lema de Providence es “What Cheer?” — de un saludo narragansett a Roger Williams.",
  },
  {
    id: "founded-1636",
    en: "Providence was founded in 1636 by Roger Williams for religious freedom.",
    es: "Providence fue fundada en 1636 por Roger Williams por la libertad religiosa.",
  },
  {
    id: "marble-dome",
    en: "The Rhode Island State House dome is among the world’s largest self-supporting marble domes.",
    es: "La cúpula del Capitolio de Rhode Island está entre las cúpulas de mármol autoportantes más grandes del mundo.",
  },
  {
    id: "waterfire",
    en: "WaterFire lights bonfires along downtown Providence rivers as public art.",
    es: "WaterFire enciende hogueras a lo largo de los ríos del centro de Providence como arte público.",
  },
  {
    id: "big-blue-bug",
    en: "Providence is home of the Big Blue Bug (a giant termite landmark) and plenty of doughnut shops.",
    es: "Providence es hogar del Big Blue Bug (un hito de termita gigante) y muchas tiendas de donas.",
  },
] as const;

export function factText(fact: ColdStartFact, locale: Locale): string {
  return locale === "es" ? fact.es : fact.en;
}

/**
 * Prefer unseen fact ids when consent Accept has stored memory; otherwise cycle
 * from `fromIndex` (wrap). Returns the chosen fact and next index hint.
 */
export function pickNextFact(
  fromIndex: number,
  options?: { preferUnseen?: boolean | undefined },
): { fact: ColdStartFact; nextIndex: number } {
  const n = COLD_START_FACTS.length;
  if (n === 0) {
    throw new Error("COLD_START_FACTS must not be empty");
  }

  const start = ((fromIndex % n) + n) % n;
  const preferUnseen = options?.preferUnseen === true;
  const seen = preferUnseen ? new Set(getSeenFactIds()) : null;

  if (seen && seen.size < n) {
    for (let offset = 0; offset < n; offset += 1) {
      const idx = (start + offset) % n;
      const candidate = COLD_START_FACTS[idx];
      if (candidate && !seen.has(candidate.id)) {
        return { fact: candidate, nextIndex: (idx + 1) % n };
      }
    }
  }

  const fact = COLD_START_FACTS[start];
  if (!fact) {
    throw new Error("COLD_START_FACTS index out of range");
  }
  return { fact, nextIndex: (start + 1) % n };
}
