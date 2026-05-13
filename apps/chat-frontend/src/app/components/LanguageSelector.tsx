import { Languages } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

interface LanguageSelectorProps {
  variant?: 'default' | 'compact';
}

export function LanguageSelector({ variant = 'default' }: LanguageSelectorProps): JSX.Element {
  const { language, setLanguage, t } = useLanguage();

  if (variant === 'compact') {
    return (
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value as 'en' | 'es')}
        className="bg-white/20 text-white border-none rounded px-2 py-1 text-xs cursor-pointer hover:bg-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all"
        aria-label={t('language')}
      >
        <option value="en" className="text-foreground bg-background">
          EN
        </option>
        <option value="es" className="text-foreground bg-background">
          ES
        </option>
      </select>
    );
  }

  return (
    <div className="relative">
      <label htmlFor="language-select" className="sr-only">
        {t('language')}
      </label>
      <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-2 rounded-lg hover:bg-accent transition-colors">
        <Languages className="w-4 h-4 sm:w-5 sm:h-5 text-foreground" aria-hidden="true" />
        <select
          id="language-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value as 'en' | 'es')}
          className="bg-background text-foreground border border-border rounded-lg px-3 py-1.5 outline-none cursor-pointer text-sm sm:text-base hover:bg-muted hover:border-primary/50 focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
          aria-label={t('language')}
        >
          <option value="en">{t('english')}</option>
          <option value="es">{t('spanish')}</option>
        </select>
      </div>
    </div>
  );
}
