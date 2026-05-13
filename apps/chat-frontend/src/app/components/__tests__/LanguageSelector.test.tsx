import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LanguageSelector } from '../LanguageSelector';
import { LanguageProvider } from '@/app/context/LanguageContext';

describe('LanguageSelector', () => {
  const renderWithProvider = () => {
    return render(
      <LanguageProvider>
        <LanguageSelector />
      </LanguageProvider>
    );
  };

  it('should render language selector', () => {
    renderWithProvider();

    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
  });

  it('should display Spanish and English options', () => {
    renderWithProvider();

    const spanishOption = screen.getByText('Español');
    const englishOption = screen.getByText('Inglés');

    expect(spanishOption).toBeInTheDocument();
    expect(englishOption).toBeInTheDocument();
  });

  it('should change language when option is selected', () => {
    renderWithProvider();

    const select = screen.getByRole('combobox') as HTMLSelectElement;

    fireEvent.change(select, { target: { value: 'en' } });
    expect(select.value).toBe('en');

    fireEvent.change(select, { target: { value: 'es' } });
    expect(select.value).toBe('es');
  });

  it('should have proper accessibility attributes', () => {
    renderWithProvider();

    const select = screen.getByRole('combobox');
    expect(select).toHaveAttribute('aria-label');
  });

  it('should render with Spanish as default', () => {
    renderWithProvider();

    const select = screen.getByRole('combobox') as HTMLSelectElement;
    expect(select.value).toBe('es');
  });
});
