import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import ChatPage from '../ChatPage';
import { useChatState } from '../../context/ChatStateContext';
import { AgentServiceError } from '../../services/agentService';

type UseAgentChatState = ReturnType<typeof useChatState>;

vi.mock('../../context/LanguageContext', () => ({
  useLanguage: () => ({
    language: 'en',
    t: (key: string) => {
      const translations: Record<string, string> = {
        appTitle: 'Vecinita',
        appSubtitle: 'Environmental & Community Information Assistant',
        newChat: 'New chat',
        welcomeMessage: 'Welcome to Vecinita',
        suggestionsStartLabel: 'Try one of these to get started',
        suggestionsFollowupLabel: 'Suggested follow-up questions',
        typePlaceholder: 'Type your question...',
        sendMessage: 'Send message',
        'error.title': 'Error',
        'error.retry': 'Retry',
      };
      return translations[key] ?? key;
    },
  }),
}));

vi.mock('../../context/ChatStateContext');

vi.mock('../../components/ChatMessage', () => ({
  ChatMessage: ({ message }: { message: { content: string } }) => (
    <div data-testid="chat-message">{message.content}</div>
  ),
}));

vi.mock('../../components/StreamingIndicator', () => ({
  StreamingIndicator: ({ message }: { message: string }) => (
    <div data-testid="streaming-indicator">{message}</div>
  ),
}));

vi.mock('../../components/ChatWidget', () => ({
  ChatWidget: () => <div data-testid="chat-widget" />,
}));

describe('ChatPage', () => {
  const mockSendMessage = vi.fn();
  const mockClearThread = vi.fn();
  const mockRetryLastMessage = vi.fn();
  const mockLoadThread = vi.fn();
  const mockStartNewConversation = vi.fn();

  const createHookState = (overrides: Partial<UseAgentChatState> = {}): UseAgentChatState => ({
    threadId: 'thread-123',
    messages: [],
    isLoading: false,
    streamingMessage: null,
    progressMessages: [],
    streamProgress: { stage: 'Working', percent: 0, waiting: false, status: 'working' },
    pendingClarification: null,
    error: null,
    splashSuggestions: ['What environmental concerns can I report in my neighborhood?'],
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
    Element.prototype.scrollTo = vi.fn();
    vi.mocked(useChatState).mockReturnValue(createHookState());
    mockSendMessage.mockResolvedValue(undefined);
  });

  it('renders title, subtitle, welcome, and chat widget', () => {
    render(<ChatPage />);

    expect(screen.getByRole('heading', { name: 'Vecinita' })).toBeInTheDocument();
    expect(screen.getByText('Environmental & Community Information Assistant')).toBeInTheDocument();
    expect(screen.getByText('Welcome to Vecinita')).toBeInTheDocument();
    expect(screen.getByTestId('chat-widget')).toBeInTheDocument();
  });

  it('renders existing conversation messages and hides the welcome state', () => {
    vi.mocked(useChatState).mockReturnValue(
      createHookState({
        messages: [
          {
            id: 'user-1',
            role: 'user',
            content: 'Can you help me find a doctor?',
            timestamp: new Date(),
          },
          {
            id: 'assistant-1',
            role: 'assistant',
            content: 'Here are a few clinics near you.',
            timestamp: new Date(),
          },
        ],
      })
    );

    render(<ChatPage />);

    expect(screen.getAllByTestId('chat-message')).toHaveLength(2);
    expect(screen.getByText('Can you help me find a doctor?')).toBeInTheDocument();
    expect(screen.getByText('Here are a few clinics near you.')).toBeInTheDocument();
    expect(screen.queryByText('Welcome to Vecinita')).not.toBeInTheDocument();
  });

  it('renders assistant response and follow-up suggestions together', () => {
    vi.mocked(useChatState).mockReturnValue(
      createHookState({
        messages: [
          {
            id: 'assistant-1',
            role: 'assistant',
            content: 'Here are a few clinics near you.',
            suggestedQuestions: ['What should I do first?'],
            timestamp: new Date(),
          },
        ],
      })
    );

    render(<ChatPage />);

    expect(screen.getByText('Here are a few clinics near you.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'What should I do first?' })).toBeInTheDocument();
  });

  it('clicking a follow-up suggestion sends message without clearing visible response', async () => {
    const user = userEvent.setup();
    vi.mocked(useChatState).mockReturnValue(
      createHookState({
        messages: [
          {
            id: 'assistant-1',
            role: 'assistant',
            content: 'Here are a few clinics near you.',
            suggestedQuestions: ['What should I do first?'],
            timestamp: new Date(),
          },
        ],
      })
    );

    render(<ChatPage />);

    await user.click(screen.getByRole('button', { name: 'What should I do first?' }));

    expect(mockSendMessage).toHaveBeenCalledWith('What should I do first?');
    expect(screen.getByText('Here are a few clinics near you.')).toBeInTheDocument();
  });

  it('does not render follow-up suggestions when assistant response is empty', () => {
    vi.mocked(useChatState).mockReturnValue(
      createHookState({
        messages: [
          {
            id: 'assistant-1',
            role: 'assistant',
            content: '   ',
            suggestedQuestions: ['What should I do first?'],
            timestamp: new Date(),
          },
        ],
      })
    );

    render(<ChatPage />);

    expect(
      screen.queryByRole('button', { name: 'What should I do first?' })
    ).not.toBeInTheDocument();
  });

  it('sends a message from submit button and clears textarea', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const textarea = screen.getByPlaceholderText('Type your question...');
    await user.type(textarea, 'Where can I find housing support?');
    await user.click(screen.getByRole('button', { name: 'Send message' }));

    expect(mockSendMessage).toHaveBeenCalledWith('Where can I find housing support?');
    expect(textarea).toHaveValue('');
  });

  it('keeps composer form and textarea full width', () => {
    render(<ChatPage />);

    const textarea = screen.getByPlaceholderText('Type your question...');
    const form = textarea.closest('form');

    expect(form).toHaveClass('w-full');
    expect(textarea).toHaveClass('w-full');
    expect(textarea).toHaveClass('min-w-0');
  });

  it('submits on Enter and keeps content on Shift+Enter', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    const textarea = screen.getByPlaceholderText('Type your question...');

    await user.type(textarea, 'Line one');
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    expect(mockSendMessage).not.toHaveBeenCalled();

    await user.keyboard('{Enter}');
    expect(mockSendMessage).toHaveBeenCalledWith('Line one\n');
  });

  it('does not submit empty messages and disables submit while loading', async () => {
    const user = userEvent.setup();
    vi.mocked(useChatState).mockReturnValue({
      ...createHookState(),
      isLoading: true,
    });

    render(<ChatPage />);

    const sendButton = screen.getByRole('button', { name: 'Send message' });
    expect(sendButton).toBeDisabled();

    const textarea = screen.getByPlaceholderText('Type your question...');
    expect(textarea).toBeDisabled();

    await user.click(sendButton);
    expect(mockSendMessage).not.toHaveBeenCalled();
  });

  it('calls clearThread when New chat is clicked', async () => {
    const user = userEvent.setup();
    render(<ChatPage />);

    await user.click(screen.getByRole('button', { name: 'New chat' }));
    expect(mockClearThread).toHaveBeenCalled();
  });

  it('does not force auto-scroll when user scrolled away from bottom', () => {
    const { rerender, container } = render(<ChatPage />);
    const messagesContainer = container.querySelector('.overflow-y-auto') as HTMLElement;

    Object.defineProperty(messagesContainer, 'scrollHeight', {
      value: 1200,
      configurable: true,
    });
    Object.defineProperty(messagesContainer, 'clientHeight', {
      value: 300,
      configurable: true,
    });
    Object.defineProperty(messagesContainer, 'scrollTop', {
      value: 100,
      configurable: true,
      writable: true,
    });

    act(() => {
      messagesContainer.dispatchEvent(new Event('scroll'));
    });
    vi.mocked(Element.prototype.scrollTo).mockClear();

    vi.mocked(useChatState).mockReturnValue(
      createHookState({
        streamingMessage: 'Thinking...',
      })
    );
    rerender(<ChatPage />);

    expect(Element.prototype.scrollTo).not.toHaveBeenCalled();
  });

  it('continues auto-scroll when user is near bottom', () => {
    const { rerender, container } = render(<ChatPage />);
    const messagesContainer = container.querySelector('.overflow-y-auto') as HTMLElement;

    Object.defineProperty(messagesContainer, 'scrollHeight', {
      value: 1200,
      configurable: true,
    });
    Object.defineProperty(messagesContainer, 'clientHeight', {
      value: 300,
      configurable: true,
    });
    Object.defineProperty(messagesContainer, 'scrollTop', {
      value: 890,
      configurable: true,
      writable: true,
    });

    act(() => {
      messagesContainer.dispatchEvent(new Event('scroll'));
    });
    vi.mocked(Element.prototype.scrollTo).mockClear();

    vi.mocked(useChatState).mockReturnValue(
      createHookState({
        streamingMessage: 'Thinking...',
      })
    );
    rerender(<ChatPage />);

    expect(Element.prototype.scrollTo).toHaveBeenCalled();
  });

  it('renders clarification prompt and questions when pending clarification exists', () => {
    vi.mocked(useChatState).mockReturnValue({
      ...createHookState(),
      pendingClarification: {
        originalQuestion: 'Please clarify your neighborhood',
        prompt: 'Please clarify your neighborhood',
        questions: ['What city are you in?', 'Do you need immediate help?'],
      },
    });

    render(<ChatPage />);

    expect(
      screen.getByText(
        (text) => text === 'Action required' || text === 'clarificationActionRequired'
      )
    ).toBeInTheDocument();
    expect(screen.getByText('Please clarify your neighborhood')).toBeInTheDocument();
    expect(screen.getByText('1. What city are you in?')).toBeInTheDocument();
    expect(screen.getByText('2. Do you need immediate help?')).toBeInTheDocument();
  });

  it('renders latest backend progress hint while loading', () => {
    vi.mocked(useChatState).mockReturnValue({
      ...createHookState(),
      isLoading: true,
      progressMessages: ['Searching', 'Scoring documents'],
      streamProgress: { stage: 'Retrieval', percent: 40, waiting: true, status: 'working' },
    });

    render(<ChatPage />);

    expect(screen.getByText('Scoring documents')).toBeInTheDocument();
    expect(screen.queryByText('Searching')).not.toBeInTheDocument();
    expect(screen.queryByText(/Connecting\s*·/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^Waiting$/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/⏳/)).not.toBeInTheDocument();
  });

  it('prefers the active streaming message over older progress hints', () => {
    vi.mocked(useChatState).mockReturnValue({
      ...createHookState(),
      isLoading: true,
      streamingMessage: 'Looking through local clinic resources...',
      progressMessages: ['Connecting', 'Searching'],
    });

    render(<ChatPage />);

    expect(screen.getByTestId('streaming-indicator')).toHaveTextContent(
      'Looking through local clinic resources...'
    );
    expect(screen.queryByText('Searching')).not.toBeInTheDocument();
  });

  it('renders error and retries last message when clicking Retry', async () => {
    const user = userEvent.setup();
    vi.mocked(useChatState).mockReturnValue({
      ...createHookState(),
      error: new AgentServiceError('Request failed', undefined, 'NETWORK_ERROR'),
    });

    render(<ChatPage />);

    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Request failed')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Retry' }));
    expect(mockRetryLastMessage).toHaveBeenCalled();
  });
});
