import { createContext, useContext, type ReactNode } from 'react';
import { useLanguage } from './LanguageContext';
import { useBackendSettings } from '../hooks/useBackendSettings';
import { useAgentChat } from '../hooks/useAgentChat';

type ChatState = ReturnType<typeof useAgentChat>;

const ChatStateContext = createContext<ChatState | null>(null);

export function ChatStateProvider({ children }: { children: ReactNode }): JSX.Element {
  const { language } = useLanguage();
  const { selectedLLM } = useBackendSettings();

  const chatState = useAgentChat({
    language: language as 'en' | 'es',
    provider: selectedLLM?.provider,
    model: selectedLLM?.model,
  });

  return <ChatStateContext.Provider value={chatState}>{children}</ChatStateContext.Provider>;
}

export function useChatState(): ChatState {
  const context = useContext(ChatStateContext);
  if (!context) {
    throw new Error('useChatState must be used within ChatStateProvider');
  }
  return context;
}
