import type { Locale } from "../hooks/useLocale.types";

const en = {
  appTitle: "Vecinita ChatRAG",
  appSubtitle: "Bilingual community Q&A — answers stay in your browser only (F3).",
  navChat: "Chat",
  navCorpus: "Corpus",
  languageGroupLabel: "Language",
  chatPanelLabel: "Community Q&A chat",
  emptyHint: "Ask a question in English or Spanish about your community.",
  roleUser: "You",
  roleAssistant: "Vecinita",
  yourQuestion: "Your question",
  questionPlaceholder: "e.g. When is the food pantry open?",
  ask: "Ask",
  asking: "Asking…",
  clearHistory: "Clear history",
  coldStartStatus:
    "The assistant is starting up — this can take up to a minute on the first question…",
  sourcesHeading: "Sources",
  corpusChunk: "Corpus chunk",
  backToChat: "Back to chat",
  corpusBrowseLabel: "Corpus browse",
  searchLabel: "Search title or URL",
  searchPlaceholder: "Search documents…",
  loadingDocuments: "Loading documents…",
  noTags: "No tags",
  openSource: "Open source",
  untitledDocument: "Untitled document",
  previous: "Previous",
  next: "Next",
  pagination: (page: number, totalPages: number, total: number) =>
    `Page ${String(page)} of ${String(totalPages)} (${String(total)} documents)`,
  loadTagsFailed: "Failed to load tags",
  loadDocumentsFailed: "Failed to load documents",
} as const;

const es = {
  appTitle: "Vecinita ChatRAG",
  appSubtitle:
    "Preguntas y respuestas bilingües — las respuestas permanecen solo en tu navegador (F3).",
  navChat: "Chat",
  navCorpus: "Corpus",
  languageGroupLabel: "Idioma",
  chatPanelLabel: "Chat de preguntas comunitarias",
  emptyHint: "Pregunta en inglés o español sobre tu comunidad.",
  roleUser: "Tú",
  roleAssistant: "Vecinita",
  yourQuestion: "Tu pregunta",
  questionPlaceholder: "p. ej. ¿Cuándo abre la despensa de alimentos?",
  ask: "Preguntar",
  asking: "Preguntando…",
  clearHistory: "Borrar historial",
  coldStartStatus:
    "El asistente se está iniciando — la primera pregunta puede tardar hasta un minuto…",
  sourcesHeading: "Fuentes",
  corpusChunk: "Fragmento del corpus",
  backToChat: "Volver al chat",
  corpusBrowseLabel: "Explorar corpus",
  searchLabel: "Buscar título o URL",
  searchPlaceholder: "Buscar documentos…",
  loadingDocuments: "Cargando documentos…",
  noTags: "Sin etiquetas",
  openSource: "Abrir fuente",
  untitledDocument: "Documento sin título",
  previous: "Anterior",
  next: "Siguiente",
  pagination: (page: number, totalPages: number, total: number) =>
    `Página ${String(page)} de ${String(totalPages)} (${String(total)} documentos)`,
  loadTagsFailed: "No se pudieron cargar las etiquetas",
  loadDocumentsFailed: "No se pudieron cargar los documentos",
} as const;

export type MessageKey = keyof typeof en;

type MessageTable = {
  [K in MessageKey]: K extends "pagination"
    ? (page: number, totalPages: number, total: number) => string
    : string;
};

export const messages: Record<Locale, MessageTable> = { en, es };

export function t(locale: Locale, key: Exclude<MessageKey, "pagination">): string;
export function t(
  locale: Locale,
  key: "pagination",
  page: number,
  totalPages: number,
  total: number,
): string;
export function t(
  locale: Locale,
  key: MessageKey,
  page?: number,
  totalPages?: number,
  total?: number,
): string {
  const table = messages[locale];
  if (key === "pagination") {
    return table.pagination(page ?? 1, totalPages ?? 1, total ?? 0);
  }
  return table[key];
}
