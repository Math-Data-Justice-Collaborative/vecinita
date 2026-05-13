export type AgentChatLocale = 'en' | 'es';

export interface AgentChatCopy {
  connecting: string;
  generating: string;
  clarificationNeeded: string;
  toolSummaryTitle: string;
  emptyResponse: string;
  unexpectedError: string;
  encounteredErrorPrefix: string;
}

export function getAgentChatCopy(locale: AgentChatLocale): AgentChatCopy {
  return {
    connecting: locale === 'es' ? 'Conectando con el backend...' : 'Connecting to backend...',
    generating: locale === 'es' ? 'Generando respuesta...' : 'Generating response...',
    clarificationNeeded: locale === 'es' ? 'Se necesita aclaración' : 'Clarification needed',
    toolSummaryTitle: locale === 'es' ? 'Resumen de herramientas' : 'Tool Summary',
    emptyResponse:
      locale === 'es'
        ? 'No pude generar una respuesta en este momento. Inténtalo de nuevo.'
        : 'I could not generate a response right now. Please try again.',
    unexpectedError:
      locale === 'es' ? 'Ocurrió un error inesperado' : 'An unexpected error occurred',
    encounteredErrorPrefix:
      locale === 'es' ? 'Lo siento, encontré un error:' : 'Sorry, I encountered an error:',
  };
}

export function localizeStreamMessage(locale: AgentChatLocale, message?: string): string {
  const raw = (message || '').trim();
  if (!raw || locale !== 'es') {
    return raw;
  }

  const exactMap: Record<string, string> = {
    'Checking if I already know this...': 'Verificando si ya conozco esto...',
    'Looking through our local resources...': 'Revisando nuestros recursos locales...',
    'I need a bit more information...': 'Necesito un poco mas de informacion...',
    'Searching for additional information...': 'Buscando informacion adicional...',
    'Let me think about your question...': 'Dejame pensar en tu pregunta...',
    'Understanding your question...': 'Entendiendo tu pregunta...',
    'Finding relevant information...': 'Encontrando informacion relevante...',
    'Finalizing answer...': 'Finalizando respuesta...',
    'User clarification is required.': 'Se requieren aclaraciones del usuario.',
    'Tool call completed.': 'Herramienta completada.',
    'I need more details to continue.': 'Necesito mas informacion para continuar.',
    'Service temporarily unavailable. Please try again in a moment.':
      'Servicio temporalmente no disponible. Intentalo de nuevo en un momento.',
  };

  if (exactMap[raw]) {
    return exactMap[raw];
  }

  const dbSearchSummary = raw.match(/^db_search returned (\d+) relevant chunks\.$/i);
  if (dbSearchSummary) {
    return `db_search devolvio ${dbSearchSummary[1]} fragmentos relevantes.`;
  }

  const webSearchSummary = raw.match(/^web_search returned (\d+) web results\.$/i);
  if (webSearchSummary) {
    return `web_search devolvio ${webSearchSummary[1]} resultados web.`;
  }

  return raw;
}

export function formatStageLabel(stage?: string): string {
  if (!stage) {
    return 'Working';
  }
  const normalized = stage.trim().toLowerCase();
  if (!normalized) {
    return 'Working';
  }
  return normalized
    .split(/[_\s-]+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function formatToolLabel(toolName: string): string {
  return toolName
    .split(/[_\s-]+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}
