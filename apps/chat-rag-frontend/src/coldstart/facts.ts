import type { Locale } from "../hooks/useLocale.types";
import { getSeenFactIds } from "./prefs";

/** Wait-catalog entry kinds (F40 facts + F64 tips/marketing; no surveys). */
export type ColdStartEntryKind = "fact" | "tip" | "marketing";

/** Curated wait-surface entry (WRWC / Providence / query tips / VECINA). */
export type ColdStartFact = {
  id: string;
  kind: ColdStartEntryKind;
  en: string;
  es: string;
};

export const COLD_START_FACTS: readonly ColdStartFact[] = [
  {
    id: "heritage-river",
    kind: "fact",
    en: "The Woonasquatucket is one of only 14 American Heritage Rivers in the U.S.",
    es: "El Woonasquatucket es uno de solo 14 ríos American Heritage en EE. UU.",
  },
  {
    id: "tip-be-specific",
    kind: "tip",
    en: "Tip: Ask a specific question — place, program, or need — for clearer answers.",
    es: "Consejo: Haz una pregunta concreta — lugar, programa o necesidad — para respuestas más claras.",
  },
  {
    id: "algonquian-name",
    kind: "fact",
    en: "“Woonasquatucket” is Algonquian — roughly “where the salt water ends.”",
    es: "“Woonasquatucket” es algonquino — aproximadamente “donde termina el agua salada.”",
  },
  {
    id: "marketing-vecina-bilingual",
    kind: "marketing",
    en: "VECINA helps neighbors find local resources in English and Spanish.",
    es: "VECINA ayuda a vecinos a encontrar recursos locales en inglés y español.",
  },
  {
    id: "wrwc-towns",
    kind: "fact",
    en: "WRWC restores the river, Greenway, and nearby communities across about six RI towns.",
    es: "WRWC restaura el río, el Greenway y comunidades cercanas en unas seis ciudades de RI.",
  },
  {
    id: "tip-topic-filter",
    kind: "tip",
    en: "Tip: Use topic filters in the menu to narrow answers to areas you care about.",
    es: "Consejo: Usa los filtros de temas en el menú para acotar respuestas a lo que te importa.",
  },
  {
    id: "river-hero",
    kind: "fact",
    en: "You can become a “River Hero” — gifts fund paths, parks, and cleaner water.",
    es: "Puedes ser un “River Hero” — las donaciones financian senderos, parques y agua más limpia.",
  },
  {
    id: "marketing-vecina-community",
    kind: "marketing",
    en: "Ask Vecinita about food pantries, rent help, ESL, clinics, and more nearby.",
    es: "Pregunta a Vecinita sobre despensas, ayuda con el alquiler, ESL, clínicas y más cerca de ti.",
  },
  {
    id: "ways-to-give",
    kind: "fact",
    en: "Ways to give include monthly gifts, stock, employer match, IRA QCD, and Fish Dedications at parks.",
    es: "Formas de donar: regalos mensuales, acciones, contrapartida del empleador, IRA QCD y dedicaciones de peces en parques.",
  },
  {
    id: "tip-either-language",
    kind: "tip",
    en: "Tip: You can ask in English or Spanish — switch language anytime in the header.",
    es: "Consejo: Puedes preguntar en inglés o español — cambia el idioma cuando quieras en el encabezado.",
  },
  {
    id: "what-cheer",
    kind: "fact",
    en: "Providence’s motto is “What Cheer?” — from a Narragansett greeting to Roger Williams.",
    es: "El lema de Providence es “What Cheer?” — de un saludo narragansett a Roger Williams.",
  },
  {
    id: "founded-1636",
    kind: "fact",
    en: "Providence was founded in 1636 by Roger Williams for religious freedom.",
    es: "Providence fue fundada en 1636 por Roger Williams por la libertad religiosa.",
  },
  {
    id: "marketing-privacy",
    kind: "marketing",
    en: "Your chat stays on this device — Vecinita does not store your questions on our servers.",
    es: "Tu chat permanece en este dispositivo — Vecinita no guarda tus preguntas en nuestros servidores.",
  },
  {
    id: "marble-dome",
    kind: "fact",
    en: "The Rhode Island State House dome is among the world’s largest self-supporting marble domes.",
    es: "La cúpula del Capitolio de Rhode Island está entre las cúpulas de mármol autoportantes más grandes del mundo.",
  },
  {
    id: "tip-follow-up",
    kind: "tip",
    en: "Tip: Follow up with “where?” or “when?” to dig into locations and hours.",
    es: "Consejo: Pregunta “¿dónde?” o “¿cuándo?” para profundizar en lugares y horarios.",
  },
  {
    id: "waterfire",
    kind: "fact",
    en: "WaterFire lights bonfires along downtown Providence rivers as public art.",
    es: "WaterFire enciende hogueras a lo largo de los ríos del centro de Providence como arte público.",
  },
  {
    id: "big-blue-bug",
    kind: "fact",
    en: "Providence is home of the Big Blue Bug (a giant termite landmark) and plenty of doughnut shops.",
    es: "Providence es hogar del Big Blue Bug (un hito de termita gigante) y muchas tiendas de donas.",
  },
] as const;

export function factText(fact: ColdStartFact, locale: Locale): string {
  return locale === "es" ? fact.es : fact.en;
}

/** Alias for typed catalog entries (fact | tip | marketing). */
export function entryText(entry: ColdStartFact, locale: Locale): string {
  return factText(entry, locale);
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
