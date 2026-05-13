import { useState, useRef, useEffect } from 'react';
import {
  Send,
  X,
  MessageSquare,
  Minimize2,
  Settings as SettingsIcon,
  RefreshCw,
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useChatState } from '../context/ChatStateContext';
import { ChatMessage } from './ChatMessage';
import { Feedback } from './MessageFeedback';
import { ThemeToggle } from './ThemeToggle';
import { LanguageSelector } from './LanguageSelector';
import { AccessibilityPanel } from './AccessibilityPanel';
import { StreamingIndicator } from './StreamingIndicator';
import { SuggestionChips } from './SuggestionChips';
import { Button } from './ui/button';
import { Separator } from './ui/separator';

interface ChatWidgetProps {
  /**
   * Position of the widget on the screen
   * @default 'bottom-right'
   */
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';

  /**
   * Primary color for the widget (overrides default turquoise)
   */
  primaryColor?: string;

  /**
   * Initial open state
   * @default false
   */
  defaultOpen?: boolean;

  /**
   * Custom welcome message
   */
  customWelcomeMessage?: string;

  /**
   * Custom widget title
   */
  title?: string;

  /**
   * Theme preference ('light' | 'dark' | 'auto')
   * @default 'auto'
   */
  themeMode?: 'light' | 'dark' | 'auto';

  /**
   * z-index for the widget
   * @default 1000
   */
  zIndex?: number;
}

export function ChatWidget({
  position = 'bottom-right',
  primaryColor,
  defaultOpen = false,
  title,
  themeMode = 'auto',
  zIndex = 1000,
}: ChatWidgetProps): JSX.Element {
  const { t } = useLanguage();
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isMinimized, setIsMinimized] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (themeMode === 'auto') {
      const saved = localStorage.getItem('vecinita-widget-theme');
      return (saved as 'light' | 'dark') || 'light';
    }
    return themeMode;
  });
  const [input, setInput] = useState('');
  const [isAccessibilityOpen, setIsAccessibilityOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Use agent chat hook with conversation storage
  const {
    messages,
    isLoading,
    streamingMessage,
    progressMessages = [],
    pendingClarification = null,
    error,
    splashSuggestions,
    sendMessage,
    retryLastMessage,
  } = useChatState();

  // Save theme to localStorage
  useEffect(() => {
    if (themeMode === 'auto') {
      localStorage.setItem('vecinita-widget-theme', theme);
    }
  }, [theme, themeMode]);

  const handleSubmit = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userInput = input;
    setInput('');

    try {
      await sendMessage(userInput);
    } catch (err) {
      console.error('Failed to send message:', err);
      // Error is handled by useAgentChat hook
    }
  };

  const handleFeedbackSubmit = (feedback: Feedback): void => {
    // Store feedback in localStorage
    const storedFeedback = localStorage.getItem('vecinita_widget_feedback');
    const feedbackData = storedFeedback ? JSON.parse(storedFeedback) : {};
    feedbackData[feedback.messageId] = {
      rating: feedback.rating,
      comment: feedback.comment,
      timestamp: feedback.timestamp.toISOString(),
    };
    localStorage.setItem('vecinita_widget_feedback', JSON.stringify(feedbackData));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleRetry = (): void => {
    retryLastMessage();
  };

  const handleSuggestionClick = async (suggestion: string): Promise<void> => {
    if (isLoading || !suggestion.trim()) {
      return;
    }

    setInput('');
    await sendMessage(suggestion);
  };

  const progressHint =
    isLoading && !streamingMessage && progressMessages.length > 0
      ? progressMessages[progressMessages.length - 1]
      : undefined;

  // Position styles
  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
  };

  const widgetTitle = title || t('appTitle');
  const widgetPrimaryColor = primaryColor || 'var(--primary)';
  const widgetForegroundColor = primaryColor ? '#ffffff' : 'var(--primary-foreground)';
  const widgetHoverColor = primaryColor
    ? 'rgb(255 255 255 / 0.2)'
    : 'color-mix(in oklab, var(--primary-foreground) 20%, transparent)';

  // Apply custom primary color if provided
  useEffect(() => {
    if (primaryColor && isOpen) {
      document.documentElement.style.setProperty('--widget-primary', primaryColor);
    }
  }, [primaryColor, isOpen]);

  if (!isOpen) {
    return (
      <Button
        onClick={() => setIsOpen(true)}
        data-testid="chat-widget-open"
        size="icon"
        className={`fixed ${positionClasses[position]} h-14 w-14 rounded-full shadow-lg transition-all hover:scale-110`}
        style={{
          backgroundColor: widgetPrimaryColor,
          color: widgetForegroundColor,
          zIndex,
        }}
        aria-label={t('newChat')}
      >
        <MessageSquare className="w-6 h-6" />
      </Button>
    );
  }

  return (
    <>
      <div
        data-testid="chat-widget-panel"
        className={`fixed ${positionClasses[position]} flex flex-col shadow-2xl rounded-lg overflow-hidden border border-border transition-all ${
          isMinimized ? 'h-14' : 'h-[600px]'
        } w-[420px] max-w-[calc(100vw-2rem)]`}
        style={{ zIndex }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-4 py-3 border-b border-border"
          style={{
            backgroundColor: widgetPrimaryColor,
            color: widgetForegroundColor,
          }}
        >
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <MessageSquare className="w-5 h-5 shrink-0" />
            <h2 className="font-medium text-sm truncate">{widgetTitle}</h2>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Button
              onClick={() => setIsAccessibilityOpen(true)}
              variant="ghost"
              size="icon"
              className="h-7 w-7 rounded"
              style={{ color: widgetForegroundColor }}
              onMouseEnter={(event) => {
                event.currentTarget.style.backgroundColor = widgetHoverColor;
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.backgroundColor = 'transparent';
              }}
              aria-label={t('accessibility')}
              title={t('accessibility')}
            >
              <SettingsIcon className="w-4 h-4" />
            </Button>
            <LanguageSelector variant="compact" />
            <ThemeToggle theme={theme} setTheme={setTheme} variant="compact" />
            <Button
              onClick={() => setIsMinimized(!isMinimized)}
              variant="ghost"
              size="icon"
              className="h-7 w-7 rounded"
              style={{ color: widgetForegroundColor }}
              onMouseEnter={(event) => {
                event.currentTarget.style.backgroundColor = widgetHoverColor;
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.backgroundColor = 'transparent';
              }}
              aria-label={isMinimized ? 'Expand' : 'Minimize'}
            >
              <Minimize2 className="w-4 h-4" />
            </Button>
            <Button
              onClick={() => setIsOpen(false)}
              variant="ghost"
              size="icon"
              className="h-7 w-7 rounded"
              style={{ color: widgetForegroundColor }}
              onMouseEnter={(event) => {
                event.currentTarget.style.backgroundColor = widgetHoverColor;
              }}
              onMouseLeave={(event) => {
                event.currentTarget.style.backgroundColor = 'transparent';
              }}
              aria-label={t('close')}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Chat Content */}
        {!isMinimized && (
          <>
            {/* Messages */}
            <div
              className={`flex-1 overflow-y-auto overscroll-contain bg-background ${theme === 'dark' ? 'dark' : ''}`}
            >
              <div className="max-w-full">
                {messages.length === 0 && (
                  <div className="px-3 pt-3 text-muted-foreground">
                    <p className="text-xs">{t('welcomeMessage')}</p>
                    <SuggestionChips
                      title={t('suggestionsStartLabel')}
                      suggestions={splashSuggestions}
                      onSelect={(suggestion) => {
                        void handleSuggestionClick(suggestion);
                      }}
                      disabled={isLoading}
                      compact
                    />
                  </div>
                )}
                {messages.map((message) => (
                  <div key={message.id}>
                    <ChatMessage message={message} onFeedbackSubmit={handleFeedbackSubmit} />
                    {message.role === 'assistant' &&
                      message.content.trim().length > 0 &&
                      (message.suggestedQuestions || []).length > 0 && (
                        <div className="px-3 pb-3">
                          <SuggestionChips
                            title={t('suggestionsFollowupLabel')}
                            suggestions={message.suggestedQuestions || []}
                            onSelect={(suggestion) => {
                              void handleSuggestionClick(suggestion);
                            }}
                            disabled={isLoading}
                            compact
                          />
                        </div>
                      )}
                  </div>
                ))}
                {(streamingMessage || progressHint) && (
                  <StreamingIndicator message={streamingMessage || progressHint} />
                )}
                {pendingClarification && (
                  <div className="mx-3 mb-3 rounded-md border border-amber-500/40 bg-amber-500/10 p-3">
                    <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-amber-700">
                      {t('clarificationActionRequired')}
                    </p>
                    <p className="text-xs text-foreground">{pendingClarification.prompt}</p>
                    {pendingClarification.questions.length > 0 && (
                      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                        {pendingClarification.questions.map((question, index) => (
                          <li key={`${index}-${question}`}>
                            {index + 1}. {question}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
                {error && (
                  <div className="p-4 m-3 bg-destructive/10 border border-destructive rounded-lg">
                    <p className="text-sm text-destructive font-medium mb-2">{t('error.title')}</p>
                    <p className="text-sm text-muted-foreground mb-3">{error.message}</p>
                    <button
                      onClick={handleRetry}
                      className="text-sm text-primary hover:underline flex items-center gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      {t('error.retry')}
                    </button>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input */}
            <Separator />
            <div className="bg-card p-3">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <textarea
                  data-testid="chat-widget-composer"
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={t('typePlaceholder')}
                  className="w-full min-w-0 flex-1 px-4 py-3 rounded-lg border border-border bg-background text-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary text-base"
                  rows={2}
                  disabled={isLoading}
                  aria-label={t('typePlaceholder')}
                />
                <Button
                  data-testid="chat-widget-send"
                  type="submit"
                  disabled={!input.trim() || isLoading}
                  size="icon"
                  className="h-9 w-9 rounded-lg hover:opacity-90"
                  style={{
                    backgroundColor: widgetPrimaryColor,
                    color: widgetForegroundColor,
                  }}
                  aria-label={t('sendMessage')}
                >
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </>
        )}
      </div>

      {/* Accessibility Panel */}
      {isAccessibilityOpen && (
        <div style={{ zIndex: zIndex + 10 }}>
          <AccessibilityPanel
            isOpen={isAccessibilityOpen}
            onClose={() => setIsAccessibilityOpen(false)}
          />
        </div>
      )}
    </>
  );
}
