import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LanguageProvider } from '@/app/context/LanguageContext';
import { ThemeToggle } from '../ThemeToggle';

function renderWithLanguage(component: React.ReactElement) {
  return render(<LanguageProvider>{component}</LanguageProvider>);
}

describe('ThemeToggle', () => {
  it('toggles from light to dark in default mode', () => {
    const setTheme = vi.fn();
    renderWithLanguage(<ThemeToggle theme="light" setTheme={setTheme} />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Modo oscuro');

    fireEvent.click(button);
    expect(setTheme).toHaveBeenCalledWith('dark');
  });

  it('toggles from dark to light in compact mode', () => {
    const setTheme = vi.fn();
    renderWithLanguage(<ThemeToggle theme="dark" setTheme={setTheme} variant="compact" />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title', 'Modo claro');

    fireEvent.click(button);
    expect(setTheme).toHaveBeenCalledWith('light');
  });

  it('renders English labels for the alternate branches', () => {
    localStorage.setItem('vecinita-language', 'en');
    const setTheme = vi.fn();

    renderWithLanguage(<ThemeToggle theme="dark" setTheme={setTheme} />);

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Light mode');
    fireEvent.click(button);
    expect(setTheme).toHaveBeenCalledWith('light');
    localStorage.removeItem('vecinita-language');
  });
});
