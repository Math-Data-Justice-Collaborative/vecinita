/**
 * NavBar — top navigation with Chat and Documents tabs.
 * Uses React Router NavLink for active-tab highlighting.
 */

import { NavLink } from 'react-router-dom';
import { MessageSquare, BookOpen, Settings } from 'lucide-react';
import { LanguageSelector } from './LanguageSelector';
import { ThemeToggle } from './ThemeToggle';

interface NavBarProps {
  theme: 'light' | 'dark';
  setTheme: (t: 'light' | 'dark') => void;
  onOpenAccessibility?: () => void;
}

export function NavBar({ theme, setTheme, onOpenAccessibility }: NavBarProps): JSX.Element {
  const linkClass = ({ isActive }: { isActive: boolean }): string =>
    [
      'flex items-center gap-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
      isActive
        ? 'bg-primary/10 text-primary'
        : 'text-muted-foreground hover:text-foreground hover:bg-accent',
    ].join(' ');

  return (
    <header className="sticky top-0 z-[2000] border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        {/* Brand */}
        <span className="text-lg font-semibold tracking-tight select-none">Vecinita</span>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={linkClass}>
            <MessageSquare size={16} />
            Chat
          </NavLink>
          <NavLink to="/documents" className={linkClass}>
            <BookOpen size={16} />
            Documents
          </NavLink>
        </nav>

        {/* Right controls */}
        <div className="flex items-center gap-2">
          <LanguageSelector />
          {onOpenAccessibility && (
            <button
              onClick={onOpenAccessibility}
              className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              aria-label="Accessibility settings"
              title="Accessibility (Alt+A)"
            >
              <Settings size={16} />
            </button>
          )}
          <ThemeToggle theme={theme} setTheme={setTheme} />
        </div>
      </div>
    </header>
  );
}
