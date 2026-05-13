import { RouterProvider } from 'react-router';
import { router } from './routes';
import { Toaster } from './components/ui/sonner';
import { getScraperConfigDiagnostic } from './api/scraper-config';
import { LocaleProvider, useLocale } from './i18n/LocaleContext';

function AppContent() {
  const scraperDiagnostic = getScraperConfigDiagnostic();
  const { t } = useLocale();

  return (
    <>
      {!scraperDiagnostic.configured && (
        <div className="border-b border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {t('app.scraperMissing')}
        </div>
      )}
      {scraperDiagnostic.configured && !scraperDiagnostic.validUrl && (
        <div className="border-b border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {t('app.scraperInvalid')}
        </div>
      )}
      <RouterProvider router={router} />
      <Toaster />
    </>
  );
}

export default function App() {
  return (
    <LocaleProvider>
      <AppContent />
    </LocaleProvider>
  );
}