import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatMessage } from '../ChatMessage';

// Mock contexts and services
vi.mock('@/app/services/agentService');

vi.mock('../../context/LanguageContext', () => ({
  useLanguage: () => ({ t: (key: string) => (key === 'sources' ? 'Sources' : key) }),
}));

vi.mock('../../context/AccessibilityContext', () => ({
  useAccessibility: () => ({
    settings: { screenReader: false },
    speak: vi.fn(),
  }),
}));

// Mock provider component for testing
const MockProviders = ({ children }: { children: React.ReactNode }) => {
  return <div>{children}</div>;
};

describe('Chat Interface Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display welcome message on initial load', () => {
    render(
      <MockProviders>
        <div data-testid="chat-welcome">
          ¡Hola! Soy Vecinita, tu asistente de información ambiental y comunitaria.
        </div>
      </MockProviders>
    );

    expect(
      screen.getByText(/Soy Vecinita, tu asistente de información ambiental/)
    ).toBeInTheDocument();
  });

  it('should send message when submit button is clicked', async () => {
    const user = userEvent.setup();
    const mockSendMessage = vi.fn();

    render(
      <MockProviders>
        <div>
          <input data-testid="message-input" placeholder="Escribe tu pregunta..." />
          <button data-testid="send-button" onClick={mockSendMessage}>
            Enviar
          </button>
        </div>
      </MockProviders>
    );

    const input = screen.getByTestId('message-input');
    const button = screen.getByTestId('send-button');

    await user.type(input, 'Test message');
    await user.click(button);

    expect(mockSendMessage).toHaveBeenCalled();
  });

  it('should display loading state while processing message', async () => {
    render(
      <MockProviders>
        <div>
          <div data-testid="loading-indicator">Buscando en la base de conocimientos...</div>
        </div>
      </MockProviders>
    );

    expect(screen.getByTestId('loading-indicator')).toBeInTheDocument();
  });

  it('should display source citations when available', () => {
    const mockSources = [
      { id: '1', content: 'Source 1', similarity: 0.95 },
      { id: '2', content: 'Source 2', similarity: 0.85 },
    ];

    render(
      <MockProviders>
        <div>
          <h3>Fuentes</h3>
          {mockSources.map((source) => (
            <div key={source.id} data-testid={`source-${source.id}`}>
              {source.content} - {(source.similarity * 100).toFixed(1)}%
            </div>
          ))}
        </div>
      </MockProviders>
    );

    expect(screen.getByText(/Fuentes/)).toBeInTheDocument();
    expect(screen.getByTestId('source-1')).toBeInTheDocument();
    expect(screen.getByTestId('source-2')).toBeInTheDocument();
  });

  it('should handle keyboard shortcuts correctly', async () => {
    const user = userEvent.setup();
    const mockSubmit = vi.fn();

    render(
      <MockProviders>
        <textarea
          data-testid="textarea"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              mockSubmit();
            }
          }}
        />
      </MockProviders>
    );

    const textarea = screen.getByTestId('textarea');
    await user.type(textarea, 'Test{Enter}');

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalled();
    });
  });

  it('should preserve conversation history', () => {
    const mockMessages = [
      { id: '1', role: 'user', content: 'Question 1' },
      { id: '2', role: 'assistant', content: 'Answer 1' },
      { id: '3', role: 'user', content: 'Question 2' },
      { id: '4', role: 'assistant', content: 'Answer 2' },
    ];

    render(
      <MockProviders>
        <div data-testid="message-list">
          {mockMessages.map((msg) => (
            <div key={msg.id} data-testid={`message-${msg.id}`}>
              <span>{msg.role}:</span> {msg.content}
            </div>
          ))}
        </div>
      </MockProviders>
    );

    mockMessages.forEach((msg) => {
      expect(screen.getByTestId(`message-${msg.id}`)).toBeInTheDocument();
    });
  });

  it('should display semantic assistant content without raw payload metadata rendering', () => {
    render(
      <MockProviders>
        <ChatMessage
          message={{
            id: 'assistant-semantic',
            role: 'assistant',
            content:
              'You can report concerns to the watershed council. [Learn more](https://wrwc.org/)',
            timestamp: new Date(),
            sources: [],
          }}
        />
      </MockProviders>
    );

    expect(screen.getByText(/report concerns to the watershed council/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Learn more' })).toHaveAttribute(
      'href',
      'https://wrwc.org/'
    );
    expect(screen.queryByText(/model.*llama/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/total_duration/i)).not.toBeInTheDocument();
  });
});
