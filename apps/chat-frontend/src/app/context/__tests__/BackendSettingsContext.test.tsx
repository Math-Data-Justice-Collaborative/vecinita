/**
 * Tests for BackendSettingsContext
 *
 * Tests backend configuration management and agent config fetching.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { BackendSettingsProvider } from '../BackendSettingsContext';
import { useBackendSettings } from '../../hooks/useBackendSettings';
import { agentService } from '../../services/agentService';
import type { AgentConfig } from '../../types/agent';

// Mock agent service
vi.mock('../../services/agentService');

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

describe('BackendSettingsContext', () => {
  const mockConfig: AgentConfig = {
    providers: [
      {
        name: 'groq',
        models: ['llama-3.1-8b-instant', 'llama-3.1-70b-versatile'],
        default: true,
      },
      {
        name: 'openai',
        models: ['gpt-4', 'gpt-3.5-turbo'],
        default: false,
      },
    ],
    models: {
      groq: ['llama-3.1-8b-instant', 'llama-3.1-70b-versatile'],
      openai: ['gpt-4', 'gpt-3.5-turbo'],
    },
    defaultProvider: 'groq',
    defaultModel: 'llama-3.1-8b-instant',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    vi.mocked(agentService.getConfig).mockResolvedValue(mockConfig);
  });

  describe('initialization', () => {
    it('should fetch config on mount', async () => {
      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(agentService.getConfig).toHaveBeenCalled();
      expect(result.current.config).toEqual(mockConfig);
    });

    it('should load saved settings from localStorage', async () => {
      const savedSettings = {
        llmProvider: 'openai',
        llmModel: 'gpt-4',
        embeddingProvider: 'openai',
        embeddingModel: 'text-embedding-3-large',
      };
      localStorage.setItem('vecinita-backend-settings', JSON.stringify(savedSettings));

      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.llmProvider).toBe('openai');
      expect(result.current.settings.llmModel).toBe('gpt-4');
    });

    it('should use default settings if none saved', async () => {
      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.llmProvider).toBe('groq');
      expect(result.current.settings.llmModel).toBe('llama-3.1-8b-instant');
    });

    it('should handle config fetch error gracefully', async () => {
      vi.mocked(agentService.getConfig).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.error).toBeTruthy();
      expect(result.current.config).toBeNull();
    });

    it('should validate saved settings against fetched config', async () => {
      const savedSettings = {
        llmProvider: 'invalid-provider',
        llmModel: 'invalid-model',
        embeddingProvider: 'huggingface',
        embeddingModel: 'test',
      };
      localStorage.setItem('vecinita-backend-settings', JSON.stringify(savedSettings));

      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      // Should reset to default provider from config
      expect(result.current.settings.llmProvider).toBe('groq');
    });
  });

  describe('setLLMProvider', () => {
    it('should update LLM provider', async () => {
      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.setLLMProvider('openai');
      });

      expect(result.current.settings.llmProvider).toBe('openai');
    });

    it('should reset model to first available for new provider', async () => {
      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.setLLMProvider('openai');
      });

      expect(result.current.settings.llmModel).toBe('gpt-4');
    });

    it('should persist settings to localStorage', async () => {
      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.setLLMProvider('openai');
      });

      const saved = localStorage.getItem('vecinita-backend-settings');
      const parsed = JSON.parse(saved!);

      expect(parsed.llmProvider).toBe('openai');
    });
  });

  describe('setLLMModel', () => {
    it('should update LLM model', async () => {
      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.setLLMModel('llama-3.1-70b-versatile');
      });

      expect(result.current.settings.llmModel).toBe('llama-3.1-70b-versatile');
    });
  });

  describe('selectedLLM', () => {
    it('should expose selected LLM as object', async () => {
      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.selectedLLM).toEqual({
        provider: 'groq',
        model: 'llama-3.1-8b-instant',
      });
    });

    it('should update when settings change', async () => {
      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.setLLMProvider('openai');
      });

      expect(result.current.selectedLLM).toEqual({
        provider: 'openai',
        model: 'gpt-4',
      });
    });
  });

  describe('refetchConfig', () => {
    it('should refetch configuration', async () => {
      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      vi.clearAllMocks();

      await act(async () => {
        await result.current.refetchConfig();
      });

      expect(agentService.getConfig).toHaveBeenCalled();
    });

    it('should clear error on successful refetch', async () => {
      vi.mocked(agentService.getConfig).mockRejectedValueOnce(new Error('Initial error'));

      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      vi.mocked(agentService.getConfig).mockResolvedValueOnce(mockConfig);

      await act(async () => {
        await result.current.refetchConfig();
      });

      expect(result.current.error).toBeNull();
      expect(result.current.config).toEqual(mockConfig);
    });
  });

  describe('error handling', () => {
    it('should set error state on fetch failure', async () => {
      vi.mocked(agentService.getConfig).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error).toContain('Failed to fetch');
    });

    it('should continue with stored settings on fetch error', async () => {
      const savedSettings = {
        llmProvider: 'groq',
        llmModel: 'llama-3.1-8b-instant',
        embeddingProvider: 'huggingface',
        embeddingModel: 'all-MiniLM-L6-v2',
      };
      localStorage.setItem('vecinita-backend-settings', JSON.stringify(savedSettings));

      vi.mocked(agentService.getConfig).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useBackendSettings(), {
        wrapper: BackendSettingsProvider,
      });

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.settings.llmProvider).toBe('groq');
      expect(result.current.error).toBeTruthy();
    });
  });

  describe('context error', () => {
    it('should throw error when used outside provider', () => {
      expect(() => {
        renderHook(() => useBackendSettings());
      }).toThrow('useBackendSettings must be used within a BackendSettingsProvider');
    });
  });
});
