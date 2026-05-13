import { useEffect, useCallback } from 'react';
import { useLanguage } from '@/app/context/LanguageContext';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  alt?: boolean;
  shift?: boolean;
  meta?: boolean;
  handler: (event: KeyboardEvent) => void;
  description: string;
  preventDefault?: boolean;
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[], enabled = true) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      for (const shortcut of shortcuts) {
        // Safety check for undefined event.key or shortcut.key
        if (!event.key || !shortcut.key) continue;

        const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatches = shortcut.ctrl
          ? event.ctrlKey || event.metaKey
          : !event.ctrlKey && !event.metaKey;
        const altMatches = shortcut.alt ? event.altKey : !event.altKey;
        const shiftMatches = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const metaMatches = shortcut.meta ? event.metaKey : !event.metaKey;

        if (keyMatches && ctrlMatches && altMatches && shiftMatches && metaMatches) {
          if (shortcut.preventDefault !== false) {
            event.preventDefault();
          }
          shortcut.handler(event);
          break;
        }
      }
    },
    [shortcuts, enabled]
  );

  useEffect(() => {
    if (enabled) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [handleKeyDown, enabled]);
}

/**
 * Hook para comandos de teclado globales de la aplicación
 */
export function useGlobalKeyboardShortcuts() {
  const { language } = useLanguage();

  const shortcuts: KeyboardShortcut[] = [
    {
      key: '/',
      ctrl: true,
      description: language === 'es' ? 'Abrir búsqueda' : 'Open search',
      handler: () => {
        const searchInput = document.querySelector('[data-search-input]') as HTMLInputElement;
        if (searchInput) {
          searchInput.focus();
        }
      },
    },
    {
      key: 'k',
      ctrl: true,
      description: language === 'es' ? 'Abrir comandos' : 'Open commands',
      handler: () => {
        const commandPalette = document.querySelector('[data-command-palette]') as HTMLElement;
        if (commandPalette) {
          commandPalette.click();
        }
      },
    },
    {
      key: 'n',
      ctrl: true,
      description: language === 'es' ? 'Nueva conversación' : 'New conversation',
      handler: () => {
        const newChatButton = document.querySelector('[data-new-chat]') as HTMLElement;
        if (newChatButton) {
          newChatButton.click();
        }
      },
    },
    {
      key: 'h',
      ctrl: true,
      shift: true,
      description: language === 'es' ? 'Ver historial' : 'View history',
      handler: () => {
        const historyButton = document.querySelector('[data-history-toggle]') as HTMLElement;
        if (historyButton) {
          historyButton.click();
        }
      },
    },
    {
      key: 's',
      ctrl: true,
      shift: true,
      description: language === 'es' ? 'Abrir configuración' : 'Open settings',
      handler: () => {
        const settingsButton = document.querySelector('[data-settings]') as HTMLElement;
        if (settingsButton) {
          settingsButton.click();
        }
      },
    },
    {
      key: 'Escape',
      description: language === 'es' ? 'Cerrar modal/panel' : 'Close modal/panel',
      handler: () => {
        const closeButton = document.querySelector('[data-close-dialog]') as HTMLElement;
        if (closeButton) {
          closeButton.click();
        }
      },
    },
  ];

  useKeyboardShortcuts(shortcuts);
}

/**
 * Hook para navegación de lista con teclado
 */
export function useListKeyboardNavigation(
  listRef: React.RefObject<HTMLElement>,
  options?: {
    onSelect?: (index: number) => void;
    loop?: boolean;
  }
) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!listRef.current) return;

      const items = Array.from(
        listRef.current.querySelectorAll('[role="option"], [role="menuitem"], [data-list-item]')
      ) as HTMLElement[];

      if (items.length === 0) return;

      const currentIndex = items.findIndex((item) => item === document.activeElement);

      let nextIndex = currentIndex;

      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault();
          nextIndex = currentIndex + 1;
          if (nextIndex >= items.length) {
            nextIndex = options?.loop ? 0 : items.length - 1;
          }
          break;

        case 'ArrowUp':
          event.preventDefault();
          nextIndex = currentIndex - 1;
          if (nextIndex < 0) {
            nextIndex = options?.loop ? items.length - 1 : 0;
          }
          break;

        case 'Home':
          event.preventDefault();
          nextIndex = 0;
          break;

        case 'End':
          event.preventDefault();
          nextIndex = items.length - 1;
          break;

        case 'Enter':
        case ' ':
          event.preventDefault();
          if (currentIndex >= 0 && options?.onSelect) {
            options.onSelect(currentIndex);
          }
          return;

        default:
          return;
      }

      if (nextIndex !== currentIndex && items[nextIndex]) {
        items[nextIndex].focus();
      }
    },
    [listRef, options]
  );

  useEffect(() => {
    const element = listRef.current;
    if (element) {
      element.addEventListener('keydown', handleKeyDown);
      return () => element.removeEventListener('keydown', handleKeyDown);
    }
  }, [listRef, handleKeyDown]);
}
