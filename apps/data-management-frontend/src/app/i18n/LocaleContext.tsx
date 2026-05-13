import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';

export type UiLocale = 'en' | 'es';

type TranslationKey =
  | 'app.scraperMissing'
  | 'app.scraperInvalid'
  | 'layout.title'
  | 'layout.subtitle'
  | 'layout.dashboard'
  | 'layout.corpus'
  | 'layout.tags'
  | 'layout.add'
  | 'layout.jobs'
  | 'layout.configuration'
  | 'layout.access'
  | 'layout.signOut'
  | 'layout.language'
  | 'layout.runtimeStatus'
  | 'layout.runtimeHint'
  | 'dashboard.title'
  | 'dashboard.subtitle'
  | 'dashboard.disclosure'
  | 'corpus.title'
  | 'corpus.subtitle'
  | 'corpus.disclosure'
  | 'corpus.refresh'
  | 'corpus.addDocument'
  | 'corpus.filtersTitle'
  | 'corpus.searchPlaceholder'
  | 'tags.title'
  | 'tags.subtitle'
  | 'tags.disclosureTopics'
  | 'tags.disclosureResources'
  | 'tags.uniqueTags'
  | 'tags.totalUsage'
  | 'tags.avgPerDocument'
  | 'tags.searchPlaceholder'
  | 'tags.all'
  | 'tags.topic'
  | 'tags.audience'
  | 'tags.geography'
  | 'tags.access'
  | 'tags.custom'
  | 'tags.schemaTitle'
  | 'tags.schemaDescription'
  | 'tags.topicCategory'
  | 'tags.empty'
  | 'tags.emptyCategory';

const STORAGE_KEY = 'vecinita.ui.locale';

const translations: Record<UiLocale, Record<TranslationKey, string>> = {
  en: {
    'app.scraperMissing': 'Scraper API is not configured. Set VITE_DM_API_BASE_URL to enable live scraping jobs.',
    'app.scraperInvalid': 'Data-management API base URL is invalid. Use a full http(s) URL in VITE_DM_API_BASE_URL.',
    'layout.title': 'Vecinita Data Admin',
    'layout.subtitle': 'Scraper and Render Postgres Data Manager',
    'layout.dashboard': 'Dashboard',
    'layout.corpus': 'Corpus',
    'layout.tags': 'Tags & Categories',
    'layout.add': 'Add Document/URL',
    'layout.jobs': 'Scrape Jobs',
    'layout.configuration': 'Configuration',
    'layout.access': 'Access & Runtime',
    'layout.signOut': 'Sign out',
    'layout.language': 'UI language',
    'layout.runtimeStatus': 'Backend API Status',
    'layout.runtimeHint': 'Set VITE_DM_API_BASE_URL to connect the data-management API',
    'dashboard.title': 'Dashboard',
    'dashboard.subtitle': 'Overview of your scraper and Render Postgres resource data',
    'dashboard.disclosure': 'This dashboard summarizes third-party resources stored for discovery. Topic labels are meant to help filtering and may be translated separately from the underlying resource language.',
    'corpus.title': 'Document Corpus',
    'corpus.subtitle': 'documents in your vector database',
    'corpus.disclosure': 'Resources listed here come from external sources. Topics and tags help discovery, but they do not imply endorsement, maintenance, or guaranteed bilingual availability.',
    'corpus.refresh': 'Refresh',
    'corpus.addDocument': 'Add Document',
    'corpus.filtersTitle': 'Filters & Search',
    'corpus.searchPlaceholder': 'Search documents...',
    'tags.title': 'Topics',
    'tags.subtitle': 'Browse translated topic labels and resource counts across your corpus',
    'tags.disclosureTopics': 'Topics are the discovery labels we attach to resources so people can filter the corpus more quickly. Resources are external websites, files, or organizations saved in the database.',
    'tags.disclosureResources': 'Vecinita does not maintain or independently verify every third-party source listed here, and some resources may only be available in one language even when topic labels are translated.',
    'tags.uniqueTags': 'Unique Tags',
    'tags.totalUsage': 'Total Usage',
    'tags.avgPerDocument': 'Avg per Resource',
    'tags.searchPlaceholder': 'Search topics...',
    'tags.all': 'All',
    'tags.topic': 'Topic',
    'tags.audience': 'Audience',
    'tags.geography': 'Geography',
    'tags.access': 'Access',
    'tags.custom': 'Custom',
    'tags.schemaTitle': 'Metadata Schema Categories',
    'tags.schemaDescription': 'Standard categories for nonprofit resource metadata',
    'tags.topicCategory': 'Topic / Category',
    'tags.empty': 'No topics found',
    'tags.emptyCategory': 'No {category} topics found',
  },
  es: {
    'app.scraperMissing': 'La API del scraper no esta configurada. Define VITE_DM_API_BASE_URL para habilitar trabajos de scraping en vivo.',
    'app.scraperInvalid': 'La URL base de la API de gestion de datos no es valida. Usa una URL http(s) completa en VITE_DM_API_BASE_URL.',
    'layout.title': 'Administracion de Datos Vecinita',
    'layout.subtitle': 'Administrador del scraper y de datos en Render Postgres',
    'layout.dashboard': 'Panel',
    'layout.corpus': 'Corpus',
    'layout.tags': 'Temas y Categorias',
    'layout.add': 'Agregar Documento/URL',
    'layout.jobs': 'Trabajos de Scraping',
    'layout.configuration': 'Configuracion',
    'layout.access': 'Acceso y Runtime',
    'layout.signOut': 'Cerrar sesion',
    'layout.language': 'Idioma de la interfaz',
    'layout.runtimeStatus': 'Estado de la API',
    'layout.runtimeHint': 'Define VITE_DM_API_BASE_URL para conectar la API de gestion de datos',
    'dashboard.title': 'Panel',
    'dashboard.subtitle': 'Resumen de los datos del scraper y de recursos en Render Postgres',
    'dashboard.disclosure': 'Este panel resume recursos de terceros guardados para descubrimiento. Las etiquetas de temas ayudan a filtrar y pueden traducirse por separado del idioma original del recurso.',
    'corpus.title': 'Corpus de Documentos',
    'corpus.subtitle': 'documentos en tu base vectorial',
    'corpus.disclosure': 'Los recursos listados aqui provienen de fuentes externas. Los temas y etiquetas ayudan al descubrimiento, pero no implican respaldo, mantenimiento ni disponibilidad bilingue garantizada.',
    'corpus.refresh': 'Actualizar',
    'corpus.addDocument': 'Agregar Documento',
    'corpus.filtersTitle': 'Filtros y Busqueda',
    'corpus.searchPlaceholder': 'Buscar documentos...',
    'tags.title': 'Temas',
    'tags.subtitle': 'Explora etiquetas traducidas de temas y conteos de recursos en tu corpus',
    'tags.disclosureTopics': 'Los temas son etiquetas de descubrimiento que asociamos a los recursos para que la gente pueda filtrar el corpus mas rapido. Los recursos son sitios web externos, archivos u organizaciones guardadas en la base de datos.',
    'tags.disclosureResources': 'Vecinita no mantiene ni verifica de forma independiente cada fuente de terceros listada aqui, y algunos recursos pueden existir solo en un idioma aunque las etiquetas de temas esten traducidas.',
    'tags.uniqueTags': 'Temas Unicos',
    'tags.totalUsage': 'Uso Total',
    'tags.avgPerDocument': 'Promedio por Recurso',
    'tags.searchPlaceholder': 'Buscar temas...',
    'tags.all': 'Todos',
    'tags.topic': 'Tema',
    'tags.audience': 'Audiencia',
    'tags.geography': 'Geografia',
    'tags.access': 'Acceso',
    'tags.custom': 'Personalizado',
    'tags.schemaTitle': 'Categorias del Esquema de Metadatos',
    'tags.schemaDescription': 'Categorias estandar para metadatos de recursos comunitarios',
    'tags.topicCategory': 'Tema / Categoria',
    'tags.empty': 'No se encontraron temas',
    'tags.emptyCategory': 'No se encontraron temas de {category}',
  },
};

interface LocaleContextValue {
  locale: UiLocale;
  setLocale: (locale: UiLocale) => void;
  t: (key: TranslationKey, vars?: Record<string, string>) => string;
}

const defaultContext: LocaleContextValue = {
  locale: 'en',
  setLocale: () => undefined,
  t: (key, vars) => {
    let value = translations.en[key] || key;
    for (const [varName, varValue] of Object.entries(vars || {})) {
      value = value.replace(`{${varName}}`, varValue);
    }
    return value;
  },
};

const LocaleContext = createContext<LocaleContextValue>(defaultContext);

function getInitialLocale(): UiLocale {
  if (typeof window === 'undefined') {
    return 'en';
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === 'en' || stored === 'es') {
    return stored;
  }

  return window.navigator.language.toLowerCase().startsWith('es') ? 'es' : 'en';
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<UiLocale>(getInitialLocale);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, locale);
    }
  }, [locale]);

  const t = (key: TranslationKey, vars?: Record<string, string>) => {
    let value = translations[locale][key] || translations.en[key] || key;
    for (const [varName, varValue] of Object.entries(vars || {})) {
      value = value.replace(`{${varName}}`, varValue);
    }
    return value;
  };

  return <LocaleContext.Provider value={{ locale, setLocale, t }}>{children}</LocaleContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useLocale() {
  return useContext(LocaleContext);
}