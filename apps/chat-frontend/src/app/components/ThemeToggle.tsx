import { Moon, Sun } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

interface ThemeToggleProps {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  variant?: 'default' | 'compact';
}

export function ThemeToggle({ theme, setTheme, variant = 'default' }: ThemeToggleProps) {
  const { t } = useLanguage();

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  if (variant === 'compact') {
    return (
      <button
        onClick={toggleTheme}
        className="p-1.5 rounded hover:bg-white/20 transition-colors"
        aria-label={theme === 'light' ? t('darkMode') : t('lightMode')}
        title={theme === 'light' ? t('darkMode') : t('lightMode')}
      >
        {theme === 'light' ? (
          <Moon className="w-4 h-4 text-white" aria-hidden="true" />
        ) : (
          <Sun className="w-4 h-4 text-white" aria-hidden="true" />
        )}
      </button>
    );
  }

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg hover:bg-accent transition-colors"
      aria-label={theme === 'light' ? t('darkMode') : t('lightMode')}
      title={theme === 'light' ? t('darkMode') : t('lightMode')}
    >
      {theme === 'light' ? (
        <Moon className="w-4 h-4 sm:w-5 sm:h-5 text-foreground" aria-hidden="true" />
      ) : (
        <Sun className="w-4 h-4 sm:w-5 sm:h-5 text-foreground" aria-hidden="true" />
      )}
    </button>
  );
}
