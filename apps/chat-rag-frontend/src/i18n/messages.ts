import type { Locale } from "../hooks/useLocale.types";

const en = {
  appTitle: "Vecinita",
  appSubtitle: "Bilingual community Q&A — answers stay in your browser only.",
  navChat: "Chat",
  navCorpus: "Corpus",
  navFeedback: "Feedback",
  feedbackTitle: "Send feedback",
  feedbackPrivacyNote:
    "Anonymous only — do not include your email, name, or other personal details.",
  feedbackCategoryLabel: "Category",
  feedbackCategory_bug: "Bug",
  feedbackCategory_wrong_answer: "Wrong answer",
  feedbackCategory_suggestion: "Suggestion",
  feedbackCategory_other: "Other",
  feedbackMessageLabel: "Message",
  feedbackMessageRequired: "Please enter a message.",
  feedbackSubmit: "Submit feedback",
  feedbackSubmitting: "Submitting…",
  feedbackSuccess: "Thanks — your feedback was submitted.",
  feedbackSubmitFailed: "Could not submit feedback. Please try again.",
  languageGroupLabel: "Language",
  chatPanelLabel: "Community Q&A chat",
  emptyHint: "Ask a question in English or Spanish about your community.",
  welcomeHeading: "What can I help with?",
  suggestedQuestionsLabel: "Try asking",
  suggestion1: "When is the food pantry open?",
  suggestion2: "How do I get rent assistance?",
  suggestion3: "Where can I find free ESL classes?",
  menuLabel: "Menu",
  toggleSidebar: "Toggle menu",
  topicsHeading: "Topics",
  themeToggleLabel: "Theme",
  switchToLight: "Switch to light theme",
  switchToDark: "Switch to dark theme",
  roleUser: "You",
  roleAssistant: "Vecinita",
  yourQuestion: "Your question",
  questionPlaceholder: "e.g. When is the food pantry open?",
  ask: "Ask",
  asking: "Asking…",
  clearHistory: "Clear history",
  newChat: "New chat",
  previousChats: "Previous chats",
  clearAllHistory: "Clear all history",
  deleteConversation: "Delete conversation",
  noPreviousChats: "No previous chats yet.",
  coldStartStatus:
    "The assistant is starting up — this can take up to a minute on the first question…",
  coldStartDonateCta: "Support the river → Donate",
  coldStartConsentLabel: "Cold-start message preferences",
  coldStartConsentCopy:
    "We’re not tracking you. We only remember which tips you’ve already seen so we don’t repeat them right away — if you allow it.",
  coldStartConsentAccept: "Accept",
  coldStartConsentOptOut: "No thanks",
  askStillStarting:
    "The assistant is still starting up. Please wait a moment and try again.",
  askStartingWait:
    "The assistant is starting up — please wait a moment and try again.",
  requestFailed: "Request failed",
  askServerError: "The assistant is temporarily unavailable. Please try again.",
  askUnauthorized: "You are not authorized to use the assistant.",
  filterByTopic: "Filter by topic",
  sourcesHeading: "Sources",
  relevancePercent: "{n}% relevant",
  relevanceTip:
    "How closely this source matched what you asked. Higher % means a stronger match.",
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
  energyEstimateLabel: "Approx. energy",
  energyCarPrefix: "≈",
  energyCarSuffix: "of average car travel",
  energyAdvisory:
    "Approximate — based on GPU TDP x utilization x wall time, not live power meters.",
  energyUseGuideToggle: "How we estimate energy",
  energyUseGuideBody:
    "Ask specific questions (place, program, or need) for clearer answers. Energy and CO2e are heuristic estimates from assumed GPU power x time — useful for context, not billing. Tip: shorter, focused questions usually finish faster.",
} as const;

const es = {
  appTitle: "Vecinita",
  appSubtitle:
    "Preguntas y respuestas bilingües — las respuestas permanecen solo en tu navegador.",
  navChat: "Chat",
  navCorpus: "Corpus",
  navFeedback: "Comentarios",
  feedbackTitle: "Enviar comentarios",
  feedbackPrivacyNote:
    "Solo anónimo — no incluyas tu correo, nombre u otros datos personales.",
  feedbackCategoryLabel: "Categoría",
  feedbackCategory_bug: "Error",
  feedbackCategory_wrong_answer: "Respuesta incorrecta",
  feedbackCategory_suggestion: "Sugerencia",
  feedbackCategory_other: "Otro",
  feedbackMessageLabel: "Mensaje",
  feedbackMessageRequired: "Escribe un mensaje.",
  feedbackSubmit: "Enviar comentarios",
  feedbackSubmitting: "Enviando…",
  feedbackSuccess: "Gracias — tus comentarios se enviaron.",
  feedbackSubmitFailed: "No se pudieron enviar. Inténtalo de nuevo.",
  languageGroupLabel: "Idioma",
  chatPanelLabel: "Chat de preguntas comunitarias",
  emptyHint: "Pregunta en inglés o español sobre tu comunidad.",
  welcomeHeading: "¿En qué puedo ayudarte?",
  suggestedQuestionsLabel: "Prueba a preguntar",
  suggestion1: "¿Cuándo abre la despensa de alimentos?",
  suggestion2: "¿Cómo obtengo ayuda con el alquiler?",
  suggestion3: "¿Dónde hay clases de inglés gratuitas?",
  menuLabel: "Menú",
  toggleSidebar: "Mostrar u ocultar el menú",
  topicsHeading: "Temas",
  themeToggleLabel: "Tema",
  switchToLight: "Cambiar a tema claro",
  switchToDark: "Cambiar a tema oscuro",
  roleUser: "Tú",
  roleAssistant: "Vecinita",
  yourQuestion: "Tu pregunta",
  questionPlaceholder: "p. ej. ¿Cuándo abre la despensa de alimentos?",
  ask: "Preguntar",
  asking: "Preguntando…",
  clearHistory: "Borrar historial",
  newChat: "Chat nuevo",
  previousChats: "Chats anteriores",
  clearAllHistory: "Borrar todo el historial",
  deleteConversation: "Eliminar conversación",
  noPreviousChats: "Aún no hay chats anteriores.",
  coldStartStatus:
    "El asistente se está iniciando — la primera pregunta puede tardar hasta un minuto…",
  coldStartDonateCta: "Apoya el río → Donar",
  coldStartConsentLabel: "Preferencias de mensajes al iniciar",
  coldStartConsentCopy:
    "No te rastreamos. Solo recordamos qué consejos ya viste para no repetirlos de inmediato — si lo permites.",
  coldStartConsentAccept: "Aceptar",
  coldStartConsentOptOut: "No, gracias",
  askStillStarting:
    "El asistente aún se está iniciando. Espera un momento e inténtalo de nuevo.",
  askStartingWait:
    "El asistente se está iniciando — espera un momento e inténtalo de nuevo.",
  requestFailed: "La solicitud falló",
  askServerError:
    "El asistente no está disponible temporalmente. Inténtalo de nuevo.",
  askUnauthorized: "No tienes autorización para usar el asistente.",
  filterByTopic: "Filtrar por tema",
  sourcesHeading: "Fuentes",
  relevancePercent: "{n}% relevante",
  relevanceTip:
    "Qué tan cerca coincidió esta fuente con lo que preguntaste. Un % más alto significa una coincidencia más fuerte.",
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
  energyEstimateLabel: "Energía aprox.",
  energyCarPrefix: "≈",
  energyCarSuffix: "de viaje en auto promedio",
  energyAdvisory:
    "Aproximado — basado en TDP de GPU x utilización x tiempo, no medidores de potencia en vivo.",
  energyUseGuideToggle: "Cómo estimamos la energía",
  energyUseGuideBody:
    "Haz preguntas concretas (lugar, programa o necesidad) para respuestas más claras. La energía y el CO2e son estimaciones heurísticas de potencia de GPU asumida x tiempo — útiles como contexto, no para facturación. Consejo: preguntas cortas y enfocadas suelen terminar antes.",
} as const;

export type MessageKey = keyof typeof en;

type MessageTable = {
  [K in MessageKey]: K extends "pagination"
    ? (page: number, totalPages: number, total: number) => string
    : string;
};

export const messages: Record<Locale, MessageTable> = { en, es };

export function t(
  locale: Locale,
  key: Exclude<MessageKey, "pagination">,
): string;
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
