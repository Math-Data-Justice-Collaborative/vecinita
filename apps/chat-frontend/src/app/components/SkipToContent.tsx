import React from 'react';
import { useLanguage } from '@/app/context/LanguageContext';

/**
 * Componente de enlace "Saltar al contenido" para accesibilidad
 */
export function SkipToContent() {
  const { language } = useLanguage();

  const handleSkip = (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    const mainContent = document.getElementById('main-content');
    if (mainContent) {
      mainContent.focus();
      mainContent.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <a
      href="#main-content"
      onClick={handleSkip}
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#4DB8B8] focus:text-white focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-[#4DB8B8]"
    >
      {language === 'es' ? 'Saltar al contenido principal' : 'Skip to main content'}
    </a>
  );
}
