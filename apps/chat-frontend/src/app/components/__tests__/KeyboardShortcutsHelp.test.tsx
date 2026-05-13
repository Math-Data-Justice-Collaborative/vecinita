import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { LanguageProvider } from '@/app/context/LanguageContext';
import { KeyboardShortcutsHelp } from '../KeyboardShortcutsHelp';

function renderHelp(onClose = vi.fn()) {
  return {
    onClose,
    ...render(
      <LanguageProvider>
        <KeyboardShortcutsHelp onClose={onClose} />
      </LanguageProvider>
    ),
  };
}

describe('KeyboardShortcutsHelp', () => {
  it('renders the modal with shortcuts and closes from the close button', () => {
    const { onClose } = renderHelp();

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Atajos de Teclado')).toBeInTheDocument();
    expect(screen.getByText('Nueva conversación')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes on escape and backdrop click', () => {
    const { onClose } = renderHelp();

    fireEvent.keyDown(window, { key: 'Enter' });
    fireEvent.keyDown(window, { key: 'Escape' });
    fireEvent.click(screen.getByRole('dialog'));

    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it('renders English copy and does not close when clicking inside the modal panel', () => {
    localStorage.setItem('vecinita-language', 'en');
    const { onClose } = renderHelp();

    expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
    expect(screen.getByText('New conversation')).toBeInTheDocument();
    expect(screen.getByText('Use Alt + K to open this help at any time.')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Keyboard Shortcuts'));
    expect(onClose).not.toHaveBeenCalled();
    localStorage.removeItem('vecinita-language');
  });
});
