import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

import { ChatWidget } from '../ChatWidget';
import { LanguageProvider } from '../../context/LanguageContext';
import { AccessibilityProvider } from '../../context/AccessibilityContext';
import { BackendSettingsProvider } from '../../context/BackendSettingsContext';
import * as chatStateContextModule from '../../context/ChatStateContext';

import { agentService } from '../../services/agentService';

vi.mock('../../services/agentService', async () => {
  const actual = await vi.importActual<typeof import('../../services/agentService')>(
    '../../services/agentService'
  );

  return {
    ...actual,
    agentService: {
      ...actual.agentService,
      askStream: vi.fn(),
      ask: vi.fn(),
      getConfig: vi.fn(),
      healthCheck: vi.fn(),
    },
  };
});
vi.mock('../../context/ChatStateContext');

vi.mock('uuid', () => ({
  v4: (() => {
    let counter = 0;
    return () => {
      counter += 1;
      return `chat-widget-test-uuid-${counter}`;
    };
  })(),
}));

function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>{children}</BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

describe('ChatWidget stream success integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    vi.mocked(agentService.getConfig).mockResolvedValue({
      providers: [{ name: 'groq', models: ['llama-3.1-8b-instant'], default: true }],
      models: { groq: ['llama-3.1-8b-instant'] },
      defaultProvider: 'groq',
      defaultModel: 'llama-3.1-8b-instant',
    });

    vi.mocked(agentService.ask).mockResolvedValue({
      answer: 'THIS SHOULD NOT BE USED',
      sources: [],
      thread_id: 'fallback-thread',
    });

    vi.mocked(chatStateContextModule.useChatState).mockReturnValue({
      threadId: 'stream-thread-1',
      messages: [
        {
          id: 'assistant-1',
          role: 'assistant',
          content: 'Real streamed answer from retrieved context.',
          timestamp: new Date(),
          sources: [],
        },
      ],
      isLoading: false,
      streamingMessage: null,
      error: null,
      progressMessages: [],
      streamProgress: { stage: 'Complete', percent: 100, waiting: false, status: 'working' },
      pendingClarification: null,
      splashSuggestions: [],
      sendMessage: vi.fn().mockResolvedValue(undefined),
      loadThread: vi.fn(),
      clearThread: vi.fn(),
      startNewConversation: vi.fn(),
      retryLastMessage: vi.fn(),
      getAllThreadIds: () => [],
      getTimeRemaining: () => null,
    });
  });

  it('renders streamed assistant response with assistant role styling and does not use fallback response', async () => {
    render(
      <TestWrapper>
        <ChatWidget defaultOpen />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Real streamed answer from retrieved context.')).toBeInTheDocument();
    });

    const assistantMessages = screen.getAllByTestId('chat-message');
    expect(
      assistantMessages.some((node) => node.getAttribute('data-message-role') === 'assistant')
    ).toBe(true);

    expect(
      screen.queryByText('I could not generate a response right now. Please try again.')
    ).not.toBeInTheDocument();
    expect(screen.queryByText('THIS SHOULD NOT BE USED')).not.toBeInTheDocument();
  });
});
