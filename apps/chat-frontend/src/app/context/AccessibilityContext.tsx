import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

interface AccessibilitySettings {
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  highContrast: boolean;
  reduceMotion: boolean;
  dyslexicFont: boolean;
  screenReader: boolean;
  highlighterMode: boolean;
}

interface AccessibilityContextType {
  settings: AccessibilitySettings;
  setFontSize: (size: AccessibilitySettings['fontSize']) => void;
  toggleHighContrast: () => void;
  toggleReduceMotion: () => void;
  toggleDyslexicFont: () => void;
  toggleScreenReader: () => void;
  toggleHighlighterMode: () => void;
  speak: (text: string) => void;
  stopSpeaking: () => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

const fontSizeMap = {
  small: '14px',
  medium: '16px',
  large: '18px',
  'extra-large': '20px',
};

export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<AccessibilitySettings>(() => {
    // Default settings
    const defaultSettings: AccessibilitySettings = {
      fontSize: 'medium',
      highContrast: false,
      reduceMotion: false,
      dyslexicFont: false,
      screenReader: false,
      highlighterMode: false,
    };

    // Load from localStorage if available
    const saved = localStorage.getItem('accessibility-settings');
    if (saved) {
      try {
        const parsedSettings = JSON.parse(saved);
        // Merge saved settings with defaults to ensure all properties exist
        return {
          ...defaultSettings,
          ...parsedSettings,
        };
      } catch {
        return defaultSettings;
      }
    }
    return defaultSettings;
  });

  useEffect(() => {
    // Save to localStorage
    localStorage.setItem('accessibility-settings', JSON.stringify(settings));

    // Apply font size
    document.documentElement.style.setProperty('--font-size', fontSizeMap[settings.fontSize]);

    // Apply high contrast
    if (settings.highContrast) {
      document.documentElement.classList.add('high-contrast');
    } else {
      document.documentElement.classList.remove('high-contrast');
    }

    // Apply reduce motion
    if (settings.reduceMotion) {
      document.documentElement.classList.add('reduce-motion');
    } else {
      document.documentElement.classList.remove('reduce-motion');
    }

    // Apply dyslexic font
    if (settings.dyslexicFont) {
      document.documentElement.classList.add('dyslexic-font');
    } else {
      document.documentElement.classList.remove('dyslexic-font');
    }

    // Apply highlighter mode
    if (settings.highlighterMode) {
      document.documentElement.classList.add('highlighter-mode');
    } else {
      document.documentElement.classList.remove('highlighter-mode');
    }
  }, [settings]);

  const setFontSize = (size: AccessibilitySettings['fontSize']) => {
    setSettings((prev) => ({ ...prev, fontSize: size }));
  };

  const toggleHighContrast = () => {
    setSettings((prev) => ({ ...prev, highContrast: !prev.highContrast }));
  };

  const toggleReduceMotion = () => {
    setSettings((prev) => ({ ...prev, reduceMotion: !prev.reduceMotion }));
  };

  const toggleDyslexicFont = () => {
    setSettings((prev) => ({ ...prev, dyslexicFont: !prev.dyslexicFont }));
  };

  const toggleScreenReader = () => {
    setSettings((prev) => ({ ...prev, screenReader: !prev.screenReader }));
  };

  const toggleHighlighterMode = () => {
    setSettings((prev) => ({ ...prev, highlighterMode: !prev.highlighterMode }));
  };

  const speak = (text: string) => {
    if (settings.screenReader) {
      const utterance = new SpeechSynthesisUtterance(text);
      speechSynthesis.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    speechSynthesis.cancel();
  };

  return (
    <AccessibilityContext.Provider
      value={{
        settings,
        setFontSize,
        toggleHighContrast,
        toggleReduceMotion,
        toggleDyslexicFont,
        toggleScreenReader,
        toggleHighlighterMode,
        speak,
        stopSpeaking,
      }}
    >
      {children}
    </AccessibilityContext.Provider>
  );
}

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (context === undefined) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
}
