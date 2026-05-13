import { createContext, useState, useEffect, ReactNode } from 'react';
import { agentService } from '../services/agentService';
import type { AgentConfig } from '../types/agent';

interface BackendSettings {
  llmProvider: string;
  llmModel: string;
  embeddingProvider: string;
  embeddingModel: string;
}

export interface BackendSettingsContextType {
  settings: BackendSettings;
  config: AgentConfig | null;
  isLoading: boolean;
  error: string | null;
  selectedLLM: { provider: string; model: string } | null;
  setLLMProvider: (provider: string) => void;
  setLLMModel: (model: string) => void;
  setEmbeddingProvider: (provider: string) => void;
  setEmbeddingModel: (model: string) => void;
  refetchConfig: () => Promise<void>;
}

export const BackendSettingsContext = createContext<BackendSettingsContextType | undefined>(
  undefined
);

export function BackendSettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<BackendSettings>(() => {
    // Default settings
    const defaultSettings: BackendSettings = {
      llmProvider: 'groq',
      llmModel: 'llama-3.1-8b-instant',
      embeddingProvider: 'huggingface',
      embeddingModel: 'sentence-transformers/all-MiniLM-L6-v2',
    };

    // Load from localStorage
    const saved = localStorage.getItem('vecinita-backend-settings');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Validate that the parsed data has the required fields
        if (
          parsed.llmProvider &&
          parsed.llmModel &&
          parsed.embeddingProvider &&
          parsed.embeddingModel
        ) {
          return parsed;
        }
        // If invalid, return defaults
        return defaultSettings;
      } catch {
        return defaultSettings;
      }
    }
    return defaultSettings;
  });

  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch agent configuration
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await agentService.getConfig();
        setConfig(data);

        // Check if saved settings are valid for current config
        if (data.providers && data.providers.length > 0) {
          setSettings((prev) => {
            const providerExists = data.providers.some(
              (provider) => provider.name === prev.llmProvider
            );

            if (!providerExists) {
              const defaultProvider =
                data.providers.find((provider) => provider.default) || data.providers[0];
              return {
                ...prev,
                llmProvider: defaultProvider.name,
                llmModel: defaultProvider.models[0] || '',
              };
            }

            const providerModels = data.models?.[prev.llmProvider] ?? [];
            if (!providerModels.includes(prev.llmModel)) {
              return {
                ...prev,
                llmModel: providerModels[0] || '',
              };
            }

            return prev;
          });
        }
      } catch (err) {
        console.error('Failed to fetch agent config:', err);
        setError('Failed to fetch backend configuration');
        // Continue with stored settings even if fetch fails
      } finally {
        setIsLoading(false);
      }
    };

    void fetchConfig();
  }, []);

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('vecinita-backend-settings', JSON.stringify(settings));
  }, [settings]);

  const setLLMProvider = (provider: string) => {
    // When provider changes, reset to first model of that provider
    const providerConfig = config?.models?.[provider];
    const firstModel = providerConfig?.[0] || '';
    setSettings((prev) => ({ ...prev, llmProvider: provider, llmModel: firstModel }));
  };

  const setLLMModel = (model: string) => {
    setSettings((prev) => ({ ...prev, llmModel: model }));
  };

  const setEmbeddingProvider = (provider: string) => {
    setSettings((prev) => ({ ...prev, embeddingProvider: provider }));
  };

  const setEmbeddingModel = (model: string) => {
    setSettings((prev) => ({ ...prev, embeddingModel: model }));
  };

  const refetchConfig = async () => {
    setIsLoading(true);
    try {
      const data = await agentService.getConfig();
      setConfig(data);
      setError(null);
    } catch {
      setError('Failed to fetch backend configuration');
    } finally {
      setIsLoading(false);
    }
  };

  // Expose selected LLM as simpler object
  const selectedLLM = {
    provider: settings.llmProvider,
    model: settings.llmModel,
  };

  return (
    <BackendSettingsContext.Provider
      value={{
        settings,
        config,
        isLoading,
        error,
        selectedLLM,
        setLLMProvider,
        setLLMModel,
        setEmbeddingProvider,
        setEmbeddingModel,
        refetchConfig,
      }}
    >
      {children}
    </BackendSettingsContext.Provider>
  );
}
