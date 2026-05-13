import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LanguageProvider } from '@/app/context/LanguageContext';
import { SkipToContent } from '../SkipToContent';

describe('SkipToContent', () => {
  it('renders the skip link in Spanish by default', () => {
    render(
      <LanguageProvider>
        <SkipToContent />
      </LanguageProvider>
    );

    expect(screen.getByRole('link', { name: 'Saltar al contenido principal' })).toBeInTheDocument();
  });

  it('focuses and scrolls the main content when clicked', () => {
    const main = document.createElement('div');
    main.id = 'main-content';
    main.tabIndex = -1;
    main.focus = vi.fn();
    main.scrollIntoView = vi.fn();
    document.body.appendChild(main);

    render(
      <LanguageProvider>
        <SkipToContent />
      </LanguageProvider>
    );

    fireEvent.click(screen.getByRole('link'));

    expect(main.focus).toHaveBeenCalled();
    expect(main.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });

    main.remove();
  });

  it('renders English text and safely handles a missing main content target', () => {
    localStorage.setItem('vecinita-language', 'en');
    render(
      <LanguageProvider>
        <SkipToContent />
      </LanguageProvider>
    );

    const link = screen.getByRole('link', { name: 'Skip to main content' });
    fireEvent.click(link);
    expect(link).toHaveAttribute('href', '#main-content');
    localStorage.removeItem('vecinita-language');
  });
});
