import { useEffect } from 'react';
import { useLanguage } from '@/app/context/LanguageContext';
import { X } from 'lucide-react';

interface Shortcut {
  keys: string[];
  description: string;
}

interface KeyboardShortcutsHelpProps {
  onClose: () => void;
}

/**
 * Componente de ayuda de atajos de teclado
 */
export function KeyboardShortcutsHelp({ onClose }: KeyboardShortcutsHelpProps): JSX.Element {
  const { language } = useLanguage();

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent): void => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEscape);
    return (): void => window.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const shortcuts: Shortcut[] = [
    {
      keys: ['Alt', 'N'],
      description: language === 'es' ? 'Nueva conversación' : 'New conversation',
    },
    {
      keys: ['Alt', 'S'],
      description: language === 'es' ? 'Abrir configuración' : 'Open settings',
    },
    {
      keys: ['Alt', 'A'],
      description: language === 'es' ? 'Abrir accesibilidad' : 'Open accessibility',
    },
    {
      keys: ['Alt', 'K'],
      description: language === 'es' ? 'Mostrar atajos de teclado' : 'Show keyboard shortcuts',
    },
    {
      keys: ['Alt', '/'],
      description: language === 'es' ? 'Enfocar entrada de mensaje' : 'Focus message input',
    },
    {
      keys: ['Enter'],
      description: language === 'es' ? 'Enviar mensaje' : 'Send message',
    },
    {
      keys: ['Shift', 'Enter'],
      description: language === 'es' ? 'Nueva línea' : 'New line',
    },
    {
      keys: ['Escape'],
      description: language === 'es' ? 'Cerrar modal/panel' : 'Close modal/panel',
    },
    {
      keys: ['Tab'],
      description: language === 'es' ? 'Navegar adelante' : 'Navigate forward',
    },
    {
      keys: ['Shift', 'Tab'],
      description: language === 'es' ? 'Navegar atrás' : 'Navigate backward',
    },
  ];

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="shortcuts-title"
    >
      <div
        className="bg-card rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-card border-b border-border px-6 py-4 flex items-center justify-between">
          <h2 id="shortcuts-title" className="text-xl font-semibold text-foreground">
            {language === 'es' ? 'Atajos de Teclado' : 'Keyboard Shortcuts'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 text-muted-foreground hover:text-foreground rounded-lg hover:bg-accent transition-colors focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label={language === 'es' ? 'Cerrar' : 'Close'}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6">
          <div className="space-y-3">
            {shortcuts.map((shortcut, index) => (
              <div
                key={index}
                className="flex items-center justify-between py-2 border-b border-border last:border-0"
              >
                <span className="text-foreground">{shortcut.description}</span>
                <div className="flex items-center gap-1">
                  {shortcut.keys.map((key, keyIndex) => (
                    <span key={keyIndex} className="flex items-center gap-1">
                      <kbd className="px-2 py-1 text-sm font-semibold text-foreground bg-muted border border-border rounded-lg">
                        {key}
                      </kbd>
                      {keyIndex < shortcut.keys.length - 1 && (
                        <span className="text-muted-foreground">+</span>
                      )}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-primary/10 rounded-lg">
            <p className="text-sm text-foreground">
              <strong>{language === 'es' ? 'Consejo:' : 'Tip:'}</strong>{' '}
              {language === 'es'
                ? 'Usa Alt + K para abrir esta ayuda en cualquier momento.'
                : 'Use Alt + K to open this help at any time.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
