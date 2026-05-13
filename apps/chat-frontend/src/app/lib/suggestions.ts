export type SuggestionContext = 'splash' | 'followup';

const FALLBACK_SUGGESTIONS: Record<'en' | 'es', Record<SuggestionContext, string[]>> = {
  en: {
    splash: [
      'What environmental concerns can I report in my neighborhood?',
      'Where can I find local housing and food assistance resources?',
      'What community programs are available near me?',
    ],
    followup: [
      'Can you summarize this in 3 key points?',
      'What should I do first?',
      'Can you suggest local resources related to this answer?',
    ],
  },
  es: {
    splash: [
      '¿Qué problemas ambientales puedo reportar en mi vecindario?',
      '¿Dónde encuentro recursos locales de vivienda y alimentos?',
      '¿Qué programas comunitarios hay cerca de mí?',
    ],
    followup: [
      '¿Puedes resumir esto en 3 puntos clave?',
      '¿Qué debería hacer primero?',
      '¿Puedes sugerir recursos locales relacionados con esta respuesta?',
    ],
  },
};

export function normalizeSuggestedQuestions(input?: string[] | null, maxItems = 3): string[] {
  if (!input || input.length === 0) {
    return [];
  }

  const seen = new Set<string>();
  const normalized: string[] = [];

  for (const value of input) {
    if (typeof value !== 'string') {
      continue;
    }

    const compact = value.trim().replace(/\s+/g, ' ');
    if (!compact) {
      continue;
    }

    const capped = compact.slice(0, 140);
    const ensuredQuestion = capped.endsWith('?') ? capped : `${capped}?`;
    const dedupeKey = ensuredQuestion.toLocaleLowerCase();

    if (seen.has(dedupeKey)) {
      continue;
    }

    seen.add(dedupeKey);
    normalized.push(ensuredQuestion);

    if (normalized.length >= maxItems) {
      break;
    }
  }

  return normalized;
}

export function getFallbackSuggestions(
  language: 'en' | 'es',
  context: SuggestionContext,
  maxItems = 3
): string[] {
  return FALLBACK_SUGGESTIONS[language][context].slice(0, maxItems);
}
