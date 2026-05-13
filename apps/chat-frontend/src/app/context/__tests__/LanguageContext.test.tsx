/**
 * Tests for LanguageContext
 *
 * Tests language switching and translation functionality.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { LanguageProvider, useLanguage } from '../LanguageContext';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

describe('LanguageContext', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('initialization', () => {
    it('should default to Spanish when no saved language', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.language).toBe('es');
    });

    it('should load saved language from localStorage', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.language).toBe('en');
    });
  });

  describe('language switching', () => {
    it('should switch from Spanish to English', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.language).toBe('es');

      act(() => {
        result.current.setLanguage('en');
      });

      expect(result.current.language).toBe('en');
    });

    it('should switch from English to Spanish', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.language).toBe('en');

      act(() => {
        result.current.setLanguage('es');
      });

      expect(result.current.language).toBe('es');
    });

    it('should persist language to localStorage', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      act(() => {
        result.current.setLanguage('en');
      });

      const saved = localStorage.getItem('vecinita-language');
      expect(saved).toBe('en');
    });
  });

  describe('translation function', () => {
    it('should translate keys correctly in English', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('appTitle')).toBe('Vecinita');
      expect(result.current.t('sendMessage')).toBe('Send message');
      expect(result.current.t('typePlaceholder')).toBe('Type your question...');
      expect(result.current.t('adminTagsPlaceholder')).toBe('Tags (comma separated, optional)');
      expect(result.current.t('adminTitle')).toBe('Admin');
      expect(result.current.t('adminTabQueue')).toBe('Queue');
    });

    it('should translate keys correctly in Spanish', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('appTitle')).toBe('Vecinita');
      expect(result.current.t('sendMessage')).toBe('Enviar mensaje');
      expect(result.current.t('typePlaceholder')).toBe('Escribe tu pregunta...');
      expect(result.current.t('adminTagsPlaceholder')).toBe(
        'Etiquetas (separadas por comas, opcional)'
      );
      expect(result.current.t('adminTitle')).toBe('Administración');
      expect(result.current.t('adminTabQueue')).toBe('Cola');
    });

    it('should return key when translation not found', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      const unknownKey = 'unknown.translation.key';
      expect(result.current.t(unknownKey)).toBe(unknownKey);
    });

    it('should update translations when language changes', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('sendMessage')).toBe('Enviar mensaje');

      act(() => {
        result.current.setLanguage('en');
      });

      expect(result.current.t('sendMessage')).toBe('Send message');
    });
  });

  describe('error translation keys', () => {
    it('should have error.title translation in English', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('error.title')).toBe('Error');
    });

    it('should have error.title translation in Spanish', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('error.title')).toBe('Error');
    });

    it('should have error.retry translation in English', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('error.retry')).toBe('Retry');
    });

    it('should have error.retry translation in Spanish', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('error.retry')).toBe('Reintentar');
    });
  });

  describe('assistant message keys', () => {
    it('should have assistant.thinking translation in English', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('assistant.thinking')).toBe('Assistant is thinking...');
    });

    it('should have assistant.thinking translation in Spanish', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('assistant.thinking')).toBe('El asistente está pensando...');
    });

    it('should have thinkingMessages translation', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      const messages = result.current.t('thinkingMessages');
      expect(messages).toContain('Searching knowledge base');
      expect(messages).toContain('Analyzing your question');
    });
  });

  describe('accessibility translations', () => {
    it('should translate accessibility keys', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('accessibility')).toBe('Accessibility');
      expect(result.current.t('fontSize')).toBe('Font size');
      expect(result.current.t('contrast')).toBe('High contrast');
      expect(result.current.t('reduceMotion')).toBe('Reduce motion');
    });
  });

  describe('backend settings translations', () => {
    it('should translate backend settings keys', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('backendSettings')).toBe('Backend Settings');
      expect(result.current.t('llmProvider')).toBe('LLM Provider');
      expect(result.current.t('llmModel')).toBe('LLM Model');
      expect(result.current.t('embeddingProvider')).toBe('Embedding Provider');
    });
  });

  describe('context error', () => {
    it('should throw error when used outside provider', () => {
      expect(() => {
        renderHook(() => useLanguage());
      }).toThrow('useLanguage must be used within a LanguageProvider');
    });
  });

  describe('common UI translations', () => {
    it('should translate common UI elements in English', () => {
      localStorage.setItem('vecinita-language', 'en');

      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('newChat')).toBe('New chat');
      expect(result.current.t('close')).toBe('Close');
      expect(result.current.t('settings')).toBe('Settings');
      expect(result.current.t('sources')).toBe('Sources');
    });

    it('should translate common UI elements in Spanish', () => {
      const { result } = renderHook(() => useLanguage(), {
        wrapper: LanguageProvider,
      });

      expect(result.current.t('newChat')).toBe('Nuevo chat');
      expect(result.current.t('close')).toBe('Cerrar');
      expect(result.current.t('settings')).toBe('Configuración');
      expect(result.current.t('sources')).toBe('Fuentes');
    });
  });
});
