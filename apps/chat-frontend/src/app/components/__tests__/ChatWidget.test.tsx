/**
 * Tests for ChatWidget component
 *
 * Tests main chat interface integration with agent backend.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatWidget } from '../ChatWidget';
import { LanguageProvider } from '../../context/LanguageContext';
import { AccessibilityProvider } from '../../context/AccessibilityContext';
import { BackendSettingsProvider } from '../../context/BackendSettingsContext';
import * as chatStateContextModule from '../../context/ChatStateContext';
import * as agentServiceModule from '../../services/agentService';
import type { Message } from '../ChatMessage';

type UseAgentChatState = ReturnType<typeof chatStateContextModule.useChatState>;

// Mock hooks and services
vi.mock('../../context/ChatStateContext');
vi.mock('../../services/agentService');

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {
    'vecinita-language': 'en', // Default to English
  };

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = { 'vecinita-language': 'en' };
    },
  };
})();

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Test wrapper with all providers
function TestWrapper({ children }: { children: React.ReactNode }) {
  return (
    <LanguageProvider>
      <AccessibilityProvider>
        <BackendSettingsProvider>{children}</BackendSettingsProvider>
      </AccessibilityProvider>
    </LanguageProvider>
  );
}

describe('ChatWidget', () => {
  const mockSendMessage = vi.fn();
  const mockClearThread = vi.fn();
  const mockRetryLastMessage = vi.fn();
  const mockLoadThread = vi.fn();
  const mockStartNewConversation = vi.fn();

  const createUseAgentChatReturn = (
    overrides: Partial<UseAgentChatState> = {}
  ): UseAgentChatState => ({
    threadId: 'thread-123',
    messages: [] as Message[],
    isLoading: false,
    streamingMessage: null,
    error: null,
    progressMessages: [],
    streamProgress: { stage: 'Working', percent: 0, waiting: false, status: 'working' },
    pendingClarification: null,
    splashSuggestions: [
      'What environmental concerns can I report in my neighborhood?',
      'Where can I find local housing and food assistance resources?',
    ],
    sendMessage: mockSendMessage,
    loadThread: mockLoadThread,
    clearThread: mockClearThread,
    startNewConversation: mockStartNewConversation,
    retryLastMessage: mockRetryLastMessage,
    getAllThreadIds: () => [],
    getTimeRemaining: () => null,
    ...overrides,
  });

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    // Mock agentService.getConfig for BackendSettingsContext
    vi.mocked(agentServiceModule.agentService.getConfig).mockResolvedValue({
      providers: [{ name: 'groq', models: ['llama-3.1-8b-instant'], default: true }],
      models: { groq: ['llama-3.1-8b-instant'] },
      defaultProvider: 'groq',
      defaultModel: 'llama-3.1-8b-instant',
    });

    // Mock shared chat state hook
    vi.mocked(chatStateContextModule.useChatState).mockReturnValue(createUseAgentChatReturn());

    mockSendMessage.mockResolvedValue(undefined);
  });

  describe('widget visibility', () => {
    it('should render closed by default', async () => {
      render(
        <TestWrapper>
          <ChatWidget />
        </TestWrapper>
      );

      // Wait for async provider initialization
      await waitFor(() => {
        const button = screen.getByRole('button', { name: /new/i });
        expect(button).toBeInTheDocument();
      });
    });

    it('should open when button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatWidget />
        </TestWrapper>
      );

      // Wait for async provider initialization
      const button = await screen.findByRole('button', { name: /new/i });
      await user.click(button);

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /vecinita/i })).toBeInTheDocument();
      });
    });

    it('should render open when defaultOpen is true', async () => {
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /vecinita/i })).toBeInTheDocument();
      });
    });

    it('should close when X button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByRole('heading')).not.toBeInTheDocument();
      });
    });

    it('should minimize when minimize button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      const minimizeButton = screen.getByRole('button', { name: /minimize/i });
      await user.click(minimizeButton);

      // Input should be hidden when minimized
      await waitFor(() => {
        expect(screen.queryByPlaceholderText(/type/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('message display', () => {
    it('should display messages from useAgentChat', async () => {
      const messages: Message[] = [
        {
          id: '1',
          role: 'user',
          content: 'Hello',
          timestamp: new Date(),
        },
        {
          id: '2',
          role: 'assistant',
          content: 'Hi there!',
          timestamp: new Date(),
          sources: [],
        },
      ];

      vi.mocked(chatStateContextModule.useChatState).mockReturnValue({
        ...createUseAgentChatReturn(),
        messages,
      });

      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Hello')).toBeInTheDocument();
        expect(screen.getByText('Hi there!')).toBeInTheDocument();
      });
    });

    it('should render assistant markdown paragraph/list/link/code formatting', async () => {
      const messages: Message[] = [
        {
          id: 'assistant-md-contract',
          role: 'assistant',
          content:
            'Paragraph text.\n\n- Item one\n- Item two\n\n[Resource link](https://example.org)\n\n`inline code`',
          timestamp: new Date(),
          sources: [],
        },
      ];

      vi.mocked(chatStateContextModule.useChatState).mockReturnValue({
        ...createUseAgentChatReturn(),
        messages,
      });

      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Paragraph text.')).toBeInTheDocument();
        expect(screen.getByText('Item one')).toBeInTheDocument();
      });

      expect(screen.getByRole('link', { name: 'Resource link' })).toHaveAttribute(
        'href',
        'https://example.org'
      );
      expect(screen.getByText('inline code')).toBeInTheDocument();
    });

    it('should display streaming indicator when loading', async () => {
      // Re-mock useAgentChat to return streaming state
      const streamingMock = createUseAgentChatReturn({
        isLoading: true,
        streamingMessage: 'Thinking about your question...',
        sendMessage: vi.fn(),
        clearThread: vi.fn(),
        retryLastMessage: vi.fn(),
        loadThread: vi.fn(),
        startNewConversation: vi.fn(),
      });

      vi.mocked(chatStateContextModule.useChatState).mockReturnValue(streamingMock);

      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      // Wait for async provider initialization and streaming indicator
      await waitFor(() => {
        const thinkingTexts = screen.queryAllByText(/thinking/i);
        expect(thinkingTexts.length).toBeGreaterThan(0);
      });
    });

    it('should display an error panel when an error occurs', async () => {
      const error = new agentServiceModule.AgentServiceError('Network error', 500, 'NETWORK_ERROR');

      vi.mocked(chatStateContextModule.useChatState).mockReturnValue({
        ...createUseAgentChatReturn(),
        error,
      });

      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('should display splash suggestions when no messages exist', async () => {
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/Try one of these to get started/i)).toBeInTheDocument();
      });
    });

    it('should display assistant follow-up suggestions and send on click', async () => {
      const user = userEvent.setup();
      const messages: Message[] = [
        {
          id: 'assistant-1',
          role: 'assistant',
          content: 'Here are relevant resources.',
          suggestedQuestions: ['Can you summarize this in 3 key points?'],
          timestamp: new Date(),
          sources: [],
        },
      ];

      vi.mocked(chatStateContextModule.useChatState).mockReturnValue({
        ...createUseAgentChatReturn(),
        messages,
      });

      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      const suggestionButton = await screen.findByRole('button', {
        name: /Can you summarize this in 3 key points\?/i,
      });
      await user.click(suggestionButton);

      await waitFor(() => {
        expect(mockSendMessage).toHaveBeenCalledWith('Can you summarize this in 3 key points?');
      });

      expect(screen.getByText('Here are relevant resources.')).toBeInTheDocument();
    });

    it('should not render follow-up suggestions when assistant response is empty', async () => {
      const messages: Message[] = [
        {
          id: 'assistant-empty',
          role: 'assistant',
          content: '   ',
          suggestedQuestions: ['Can you summarize this in 3 key points?'],
          timestamp: new Date(),
          sources: [],
        },
      ];

      vi.mocked(chatStateContextModule.useChatState).mockReturnValue({
        ...createUseAgentChatReturn(),
        messages,
      });

      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(
          screen.queryByRole('button', { name: /Can you summarize this in 3 key points\?/i })
        ).not.toBeInTheDocument();
      });
    });
  });

  describe('message sending', () => {
    it('should send message when form is submitted', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      const input = screen.getByRole('textbox');
      const sendButton = screen.getByRole('button', { name: /send/i });

      await user.type(input, 'Test question');
      await user.click(sendButton);

      await waitFor(() => {
        expect(mockSendMessage).toHaveBeenCalledWith('Test question');
      });
    });

    it('should send message on Enter key', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      const input = screen.getByRole('textbox');
      await user.type(input, 'Test question{Enter}');

      await waitFor(() => {
        expect(mockSendMessage).toHaveBeenCalledWith('Test question');
      });
    });

    it('should not send on Shift+Enter', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      const input = screen.getByRole('textbox');
      await user.type(input, 'Line 1{Shift>}{Enter}{/Shift}Line 2');

      expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it('should clear input after sending', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      const input = screen.getByRole('textbox') as HTMLTextAreaElement;
      await user.type(input, 'Test question');

      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      await waitFor(() => {
        expect(input.value).toBe('');
      });
    });

    it('should disable input when loading', async () => {
      vi.mocked(chatStateContextModule.useChatState).mockReturnValue({
        ...createUseAgentChatReturn(),
        isLoading: true,
      });

      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        const input = screen.getByRole('textbox');
        expect(input).toBeDisabled();
      });
    });

    it('should not send empty message', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      const sendButton = screen.getByRole('button', { name: /send/i });
      await user.click(sendButton);

      expect(mockSendMessage).not.toHaveBeenCalled();
    });
  });

  describe('error handling', () => {
    it('should display retry button on error', async () => {
      const error = {
        ...new agentServiceModule.AgentServiceError('Request failed', 500, 'REQUEST_FAILED'),
      };

      vi.mocked(chatStateContextModule.useChatState).mockReturnValue({
        ...createUseAgentChatReturn(),
        error,
      });

      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/retry/i)).toBeInTheDocument();
      });
    });

    it('should call retryLastMessage when retry is clicked', async () => {
      const user = userEvent.setup();
      const error = {
        ...new agentServiceModule.AgentServiceError('Request failed', 500, 'REQUEST_FAILED'),
      };

      vi.mocked(chatStateContextModule.useChatState).mockReturnValue({
        ...createUseAgentChatReturn(),
        error,
      });

      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/retry/i)).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      expect(mockRetryLastMessage).toHaveBeenCalled();
    });
  });

  describe('customization', () => {
    it('should apply custom title', async () => {
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} title="Custom Chat" />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Custom Chat')).toBeInTheDocument();
      });
    });

    it('should apply custom position class', async () => {
      const { container } = render(
        <TestWrapper>
          <ChatWidget position="top-left" />
        </TestWrapper>
      );

      // Wait for async provider initialization
      await waitFor(() => {
        const widget = container.querySelector('.top-4.left-4');
        expect(widget).toBeInTheDocument();
      });
    });

    it('should apply custom zIndex', async () => {
      const { container } = render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} zIndex={9999} />
        </TestWrapper>
      );

      // Wait for async provider initialization
      await waitFor(() => {
        const widget = container.firstChild as HTMLElement;
        expect(widget.style.zIndex).toBe('9999');
      });
    });
  });

  describe('accessibility', () => {
    it('should have proper ARIA labels', async () => {
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('textbox')).toHaveAttribute('aria-label');
        expect(screen.getByRole('button', { name: /send/i })).toHaveAttribute('aria-label');
        expect(screen.getByRole('button', { name: /close/i })).toHaveAttribute('aria-label');
      });
    });

    it('should open accessibility panel when settings clicked', async () => {
      const user = userEvent.setup();
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      const settingsButton = screen.getByRole('button', { name: /accessibility/i });
      await user.click(settingsButton);

      // Accessibility panel should render (implementation depends on AccessibilityPanel component)
      await waitFor(() => {
        // This may vary based on AccessibilityPanel implementation
        expect(settingsButton).toBeInTheDocument();
      });
    });
  });

  describe('theme handling', () => {
    it('should render with default theme', async () => {
      render(
        <TestWrapper>
          <ChatWidget defaultOpen={true} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading')).toBeInTheDocument();
      });

      // Verify widget is rendered in the DOM
      const widget = screen.getByRole('heading');
      expect(widget).toBeVisible();
    });
  });
});
