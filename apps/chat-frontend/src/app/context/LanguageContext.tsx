import React, { createContext, useContext, useState, ReactNode } from 'react';

type Language = 'en' | 'es';

interface Translations {
  [key: string]: {
    en: string;
    es: string;
  };
}

const translations: Translations = {
  appTitle: {
    en: 'Vecinita',
    es: 'Vecinita',
  },
  appSubtitle: {
    en: 'Environmental & Community Information Assistant',
    es: 'Asistente de Información Ambiental y Comunitaria',
  },
  sendMessage: {
    en: 'Send message',
    es: 'Enviar mensaje',
  },
  typePlaceholder: {
    en: 'Type your question...',
    es: 'Escribe tu pregunta...',
  },
  sources: {
    en: 'Sources',
    es: 'Fuentes',
  },
  darkMode: {
    en: 'Dark mode',
    es: 'Modo oscuro',
  },
  lightMode: {
    en: 'Light mode',
    es: 'Modo claro',
  },
  language: {
    en: 'Language',
    es: 'Idioma',
  },
  english: {
    en: 'English',
    es: 'Inglés',
  },
  spanish: {
    en: 'Spanish',
    es: 'Español',
  },
  welcomeMessage: {
    en: "Hello! I'm Vecinita, your environmental and community information assistant. I can help you find information about environmental and community topics. Ask me anything!",
    es: '¡Hola! Soy Vecinita, tu asistente de información ambiental y comunitaria. Puedo ayudarte a encontrar información sobre temas ambientales y comunitarios. ¡Pregúntame lo que quieras!',
  },
  suggestionsStartLabel: {
    en: 'Try one of these to get started',
    es: 'Prueba una de estas para comenzar',
  },
  suggestionsFollowupLabel: {
    en: 'Suggested follow-up questions',
    es: 'Preguntas sugeridas para continuar',
  },
  newChat: {
    en: 'New chat',
    es: 'Nuevo chat',
  },
  settings: {
    en: 'Settings',
    es: 'Configuración',
  },
  accessibility: {
    en: 'Accessibility',
    es: 'Accesibilidad',
  },
  fontSize: {
    en: 'Font size',
    es: 'Tamaño de fuente',
  },
  contrast: {
    en: 'High contrast',
    es: 'Alto contraste',
  },
  reduceMotion: {
    en: 'Reduce motion',
    es: 'Reducir movimiento',
  },
  close: {
    en: 'Close',
    es: 'Cerrar',
  },
  small: {
    en: 'Small',
    es: 'Pequeño',
  },
  medium: {
    en: 'Medium',
    es: 'Mediano',
  },
  large: {
    en: 'Large',
    es: 'Grande',
  },
  extraLarge: {
    en: 'Extra Large',
    es: 'Extra Grande',
  },
  fontSizeDescription: {
    en: 'Adjust the size of text throughout the application.',
    es: 'Ajusta el tamaño del texto en toda la aplicación.',
  },
  highContrastMode: {
    en: 'High contrast mode',
    es: 'Modo de alto contraste',
  },
  highContrastDescription: {
    en: 'Increase color contrast for better visibility.',
    es: 'Aumenta el contraste de color para mejor visibilidad.',
  },
  reduceMotionMode: {
    en: 'Reduce motion',
    es: 'Reducir movimiento',
  },
  reduceMotionDescription: {
    en: 'Minimize animations and transitions.',
    es: 'Minimiza animaciones y transiciones.',
  },
  keyboardShortcuts: {
    en: 'Keyboard Shortcuts',
    es: 'Atajos de Teclado',
  },
  newLine: {
    en: 'New line',
    es: 'Nueva línea',
  },
  closePanel: {
    en: 'Close panel',
    es: 'Cerrar panel',
  },
  thinkingMessages: {
    en: 'Searching knowledge base...|Analyzing your question...|Finding relevant sources...|Preparing response...',
    es: 'Buscando en la base de conocimientos...|Analizando tu pregunta...|Encontrando fuentes relevantes...|Preparando respuesta...',
  },
  llmModel: {
    en: 'LLM Model',
    es: 'Modelo LLM',
  },
  llmModelDescription: {
    en: 'Select the language model for generating responses.',
    es: 'Selecciona el modelo de lenguaje para generar respuestas.',
  },
  embeddingService: {
    en: 'Embedding Service',
    es: 'Servicio de Embeddings',
  },
  embeddingServiceDescription: {
    en: 'Select the embedding service for vector search.',
    es: 'Selecciona el servicio de embeddings para búsqueda vectorial.',
  },
  llmProvider: {
    en: 'LLM Provider',
    es: 'Proveedor LLM',
  },
  llmProviderDescription: {
    en: 'Select the provider for language models.',
    es: 'Selecciona el proveedor de modelos de lenguaje.',
  },
  embeddingProvider: {
    en: 'Embedding Provider',
    es: 'Proveedor de Embeddings',
  },
  embeddingProviderDescription: {
    en: 'Select the provider for embedding models.',
    es: 'Selecciona el proveedor de modelos de embeddings.',
  },
  backendSettings: {
    en: 'Backend Settings',
    es: 'Configuración del Backend',
  },
  documentDetails: {
    en: 'Document Details',
    es: 'Detalles del Documento',
  },
  metadata: {
    en: 'Metadata',
    es: 'Metadatos',
  },
  createdAt: {
    en: 'Created At',
    es: 'Fecha de Creación',
  },
  documentId: {
    en: 'Document ID',
    es: 'ID del Documento',
  },
  openSource: {
    en: 'Open Source',
    es: 'Abrir Fuente',
  },
  dyslexicFont: {
    en: 'Dyslexic Font',
    es: 'Fuente para Dislexia',
  },
  dyslexicFontMode: {
    en: 'Dyslexic-friendly font',
    es: 'Fuente amigable para dislexia',
  },
  dyslexicFontDescription: {
    en: 'Use a font designed to improve readability for people with dyslexia.',
    es: 'Usa una fuente diseñada para mejorar la legibilidad para personas con dislexia.',
  },
  screenReader: {
    en: 'Screen Reader',
    es: 'Lector de Pantalla',
  },
  screenReaderMode: {
    en: 'Text-to-speech mode',
    es: 'Modo de texto a voz',
  },
  screenReaderDescription: {
    en: 'Enable text-to-speech for messages and UI elements.',
    es: 'Activa texto a voz para mensajes y elementos de la interfaz.',
  },
  highlighterMode: {
    en: 'Highlighter Mode',
    es: 'Modo Resaltador',
  },
  highlighterModeDescription: {
    en: 'Highlight text on hover to improve reading focus.',
    es: 'Resalta el texto al pasar el cursor para mejorar el enfoque de lectura.',
  },
  'assistant.thinking': {
    en: 'Assistant is thinking...',
    es: 'El asistente está pensando...',
  },
  'error.title': {
    en: 'Error',
    es: 'Error',
  },
  'error.retry': {
    en: 'Retry',
    es: 'Reintentar',
  },
  clarificationActionRequired: {
    en: 'Action required',
    es: 'Acción requerida',
  },
  documentsTitle: {
    en: 'Documents',
    es: 'Documentos',
  },
  documentsSubtitle: {
    en: 'Community resources and reference materials available to everyone.',
    es: 'Recursos comunitarios y materiales de referencia disponibles para todas las personas.',
  },
  docsTotalSources: {
    en: 'Community Sources',
    es: 'Fuentes Comunitarias',
  },
  docsTotalTopics: {
    en: 'Topics',
    es: 'Temas',
  },
  docsVisibleResources: {
    en: 'Visible Resources',
    es: 'Recursos Visibles',
  },
  docsResources: {
    en: 'Resources',
    es: 'Recursos',
  },
  docsSearchPlaceholder: {
    en: 'Search resources…',
    es: 'Buscar recursos…',
  },
  docsTopics: {
    en: 'Topics',
    es: 'Temas',
  },
  docsClearFilters: {
    en: 'Clear filters',
    es: 'Limpiar filtros',
  },
  docsNoTopics: {
    en: 'No topics available yet.',
    es: 'Aún no hay temas disponibles.',
  },
  docsSourcesLabel: {
    en: 'sources',
    es: 'fuentes',
  },
  docsResource: {
    en: 'Resource',
    es: 'Recurso',
  },
  docsActions: {
    en: 'Actions',
    es: 'Acciones',
  },
  docsNoResults: {
    en: 'No resources match your filters.',
    es: 'Ningún recurso coincide con tus filtros.',
  },
  docsOpenSource: {
    en: 'Open source',
    es: 'Abrir fuente',
  },
  docsDownload: {
    en: 'Download',
    es: 'Descargar',
  },
  docsLoading: {
    en: 'Loading resources…',
    es: 'Cargando recursos…',
  },
  docsLoadFailed: {
    en: 'Failed to load resources',
    es: 'Error al cargar recursos',
  },
  docsUnknownError: {
    en: 'Unknown error',
    es: 'Error desconocido',
  },
  docsDownloadError: {
    en: 'Unable to resolve a download link',
    es: 'No se pudo resolver un enlace de descarga',
  },
  docsNoDownloadAvailable: {
    en: 'This resource does not have a downloadable file.',
    es: 'Este recurso no tiene un archivo descargable.',
  },
  docsDownloadFailed: {
    en: 'Failed to download resource',
    es: 'Error al descargar el recurso',
  },
  adminTagsPlaceholder: {
    en: 'Tags (comma separated, optional)',
    es: 'Etiquetas (separadas por comas, opcional)',
  },
  adminTagsAutocompleteHint: {
    en: 'Autocomplete from existing tags. You can add custom tags.',
    es: 'Autocompletado con etiquetas existentes. Puedes agregar etiquetas personalizadas.',
  },
  adminEditTagsTitle: {
    en: 'Edit tags',
    es: 'Editar etiquetas',
  },
  adminSave: {
    en: 'Save',
    es: 'Guardar',
  },
  adminTitle: {
    en: 'Admin',
    es: 'Administración',
  },
  adminSubtitle: {
    en: 'Manage corpus sources, upload documents, and monitor the scraper queue.',
    es: 'Administra fuentes del corpus, sube documentos y supervisa la cola del scraper.',
  },
  adminTabSources: {
    en: 'Sources',
    es: 'Fuentes',
  },
  adminTabUpload: {
    en: 'Upload',
    es: 'Subir',
  },
  adminTabQueue: {
    en: 'Queue',
    es: 'Cola',
  },
  adminTabModels: {
    en: 'Models',
    es: 'Modelos',
  },
  adminCheckingPermissions: {
    en: 'Checking permissions…',
    es: 'Verificando permisos…',
  },
  adminAddNewSource: {
    en: 'Add New Source',
    es: 'Agregar nueva fuente',
  },
  adminBatchIngestTitle: {
    en: 'Batch URL Ingest',
    es: 'Ingesta masiva de URL',
  },
  adminBatchUrlsPlaceholder: {
    en: 'Paste urls.txt content (one URL per line)',
    es: 'Pega el contenido de urls.txt (una URL por línea)',
  },
  adminBatchTagModeLabel: {
    en: 'Tag mode',
    es: 'Modo de etiquetas',
  },
  adminBatchTagModeAutoInfer: {
    en: 'Auto-infer + baseline tags',
    es: 'Auto-inferir + etiquetas base',
  },
  adminBatchIngest: {
    en: 'Batch ingest',
    es: 'Ingesta masiva',
  },
  adminBatchResult: {
    en: 'Batch ingest: {completed}/{submitted} completed ({failed} failed).',
    es: 'Ingesta masiva: {completed}/{submitted} completadas ({failed} fallidas).',
  },
  adminCrawlDepth: {
    en: 'Crawl depth',
    es: 'Profundidad de rastreo',
  },
  adminDepth: {
    en: 'Depth',
    es: 'Profundidad',
  },
  adminAdd: {
    en: 'Add',
    es: 'Agregar',
  },
  adminRefresh: {
    en: 'Refresh',
    es: 'Actualizar',
  },
  adminSource: {
    en: 'Source',
    es: 'Fuente',
  },
  adminTags: {
    en: 'Tags',
    es: 'Etiquetas',
  },
  adminChunks: {
    en: 'Chunks',
    es: 'Fragmentos',
  },
  adminLoading: {
    en: 'Loading…',
    es: 'Cargando…',
  },
  adminNoSourcesYet: {
    en: 'No sources yet.',
    es: 'Aún no hay fuentes.',
  },
  adminDeleteChunks: {
    en: 'Delete chunks',
    es: 'Eliminar fragmentos',
  },
  adminDeleteChunksConfirm: {
    en: 'Delete all chunks for:',
    es: 'Eliminar todos los fragmentos de:',
  },
  adminSourcesCount: {
    en: 'sources',
    es: 'fuentes',
  },
  adminAddedSourceIndexed: {
    en: 'Added source and indexed {count} chunks.',
    es: 'Se agregó la fuente y se indexaron {count} fragmentos.',
  },
  adminQueuedSource: {
    en: 'Queued: {url}',
    es: 'En cola: {url}',
  },
  adminDeletedChunks: {
    en: 'Deleted {count} chunks.',
    es: 'Se eliminaron {count} fragmentos.',
  },
  adminDropFile: {
    en: 'Drop a file here or click to select',
    es: 'Suelta un archivo aquí o haz clic para seleccionarlo',
  },
  adminUploadMaxInfo: {
    en: 'PDF, TXT, HTML, Markdown — max 50 MB',
    es: 'PDF, TXT, HTML, Markdown — máximo 50 MB',
  },
  adminUnknownType: {
    en: 'unknown type',
    es: 'tipo desconocido',
  },
  adminUploading: {
    en: 'Uploading…',
    es: 'Subiendo…',
  },
  adminUploadAndEmbed: {
    en: 'Upload & Embed',
    es: 'Subir e indexar',
  },
  adminUploadedChunksInserted: {
    en: 'Uploaded: {count} chunks inserted.',
    es: 'Subido: {count} fragmentos insertados.',
  },
  adminUploadHelp: {
    en: 'Uploaded files are chunked (1000 chars / 200 overlap), embedded, and inserted into the Postgres corpus automatically. Use the Queue tab to monitor progress for URL-based sources.',
    es: 'Los archivos subidos se dividen en fragmentos (1000 caracteres / 200 de superposición), se vectorizan y se insertan automáticamente en el corpus de Postgres. Usa la pestaña Cola para supervisar el progreso de las fuentes por URL.',
  },
  adminAllStatuses: {
    en: 'All statuses',
    es: 'Todos los estados',
  },
  adminPending: {
    en: 'Pending',
    es: 'Pendiente',
  },
  adminProcessing: {
    en: 'Processing',
    es: 'Procesando',
  },
  adminRunning: {
    en: 'Running',
    es: 'En ejecución',
  },
  adminCompleted: {
    en: 'Completed',
    es: 'Completado',
  },
  adminFailed: {
    en: 'Failed',
    es: 'Fallido',
  },
  adminAutoRefresh: {
    en: 'Auto-refresh 10 s',
    es: 'Autoactualizar cada 10 s',
  },
  adminType: {
    en: 'Type',
    es: 'Tipo',
  },
  adminStatus: {
    en: 'Status',
    es: 'Estado',
  },
  adminProgress: {
    en: 'Progress',
    es: 'Progreso',
  },
  adminCreated: {
    en: 'Created',
    es: 'Creado',
  },
  adminNoJobs: {
    en: 'No jobs.',
    es: 'No hay trabajos.',
  },
  adminFileType: {
    en: 'file',
    es: 'archivo',
  },
  adminFailedJobs: {
    en: 'Failed jobs:',
    es: 'Trabajos fallidos:',
  },
  adminChunksLabel: {
    en: 'Chunks:',
    es: 'Fragmentos:',
  },
  adminModelConfigUpdated: {
    en: 'Model configuration updated.',
    es: 'La configuración del modelo se actualizó.',
  },
  adminLoadingModelSettings: {
    en: 'Loading model settings…',
    es: 'Cargando configuración de modelos…',
  },
  adminModelConfiguration: {
    en: 'Model Configuration',
    es: 'Configuración de modelos',
  },
  adminGenerationModel: {
    en: 'Generation Model',
    es: 'Modelo de generación',
  },
  adminEmbeddingModel: {
    en: 'Embedding Model',
    es: 'Modelo de embeddings',
  },
  adminSelectProvider: {
    en: 'Select provider',
    es: 'Seleccionar proveedor',
  },
  adminSelectModel: {
    en: 'Select model',
    es: 'Seleccionar modelo',
  },
  adminSaveModelSettings: {
    en: 'Save model settings',
    es: 'Guardar configuración de modelos',
  },
};

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    // Load from localStorage, default to Spanish
    const saved = localStorage.getItem('vecinita-language');
    return (saved as Language) || 'es';
  });

  // Save to localStorage when language changes
  React.useEffect(() => {
    localStorage.setItem('vecinita-language', language);
  }, [language]);

  const t = (key: string): string => {
    return translations[key]?.[language] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
