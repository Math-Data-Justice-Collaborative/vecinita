/**
 * ChatPage — full-page chat experience plus floating widget.
 * This is the "/" route.
 */

import { useEffect, useRef, useState } from 'react';
import { Fragment } from 'react';
import { MessageSquare, RefreshCw, Send } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { useChatState } from '../context/ChatStateContext';
import { ChatMessage } from '../components/ChatMessage';
import { StreamingIndicator } from '../components/StreamingIndicator';
import { SuggestionChips } from '../components/SuggestionChips';
import { ChatWidget } from '../components/ChatWidget';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardFooter, CardHeader } from '../components/ui/card';
import { Separator } from '../components/ui/separator';

export default function ChatPage() {
  const { t } = useLanguage();
  const [input, setInput] = useState('');
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [shouldStickToBottom, setShouldStickToBottom] = useState(true);

  const {
    messages,
    isLoading,
    streamingMessage,
    progressMessages,
    pendingClarification,
    error,
    splashSuggestions,
    sendMessage,
    clearThread,
    retryLastMessage,
  } = useChatState();

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) {
      return;
    }

    const onScroll = () => {
      const distanceFromBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight;
      setShouldStickToBottom(distanceFromBottom < 120);
    };

    container.addEventListener('scroll', onScroll);
    onScroll();

    return () => {
      container.removeEventListener('scroll', onScroll);
    };
  }, []);

  useEffect(() => {
    if (!shouldStickToBottom) {
      return;
    }

    const container = messagesContainerRef.current;
    if (!container) {
      return;
    }

    // Keep scrolling constrained to the chat container instead of the page viewport.
    container.scrollTo?.({ top: container.scrollHeight, behavior: 'smooth' });
  }, [messages, streamingMessage, shouldStickToBottom]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!input.trim() || isLoading) {
      return;
    }
    const question = input;
    setInput('');
    setShouldStickToBottom(true);
    await sendMessage(question);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit(event);
    }
  };

  const handleSuggestionClick = async (suggestion: string) => {
    if (isLoading || !suggestion.trim()) {
      return;
    }

    setInput('');
    setShouldStickToBottom(true);
    await sendMessage(suggestion);
  };

  const progressHint =
    isLoading && !streamingMessage && progressMessages.length > 0
      ? progressMessages[progressMessages.length - 1]
      : undefined;

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 py-6">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{t('appTitle')}</h1>
          <p className="text-sm text-muted-foreground">{t('appSubtitle')}</p>
        </div>
        <Button onClick={() => clearThread()} variant="outline" size="sm" type="button">
          {t('newChat')}
        </Button>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden shadow-sm">
        <CardHeader className="p-0" />
        <CardContent className="flex-1 p-0">
          <div
            ref={messagesContainerRef}
            className="h-full overflow-y-auto overscroll-contain pb-2"
            data-testid="chat-page-messages-container"
          >
            {messages.length === 0 && (
              <div className="p-8 text-center text-muted-foreground">
                <MessageSquare className="mx-auto mb-3 h-6 w-6" />
                <p className="text-sm">{t('welcomeMessage')}</p>
                <SuggestionChips
                  title={t('suggestionsStartLabel')}
                  suggestions={splashSuggestions}
                  onSelect={(suggestion) => {
                    void handleSuggestionClick(suggestion);
                  }}
                  disabled={isLoading}
                />
              </div>
            )}

            {messages.map((message) => (
              <Fragment key={message.id}>
                <ChatMessage message={message} />
                {message.role === 'assistant' &&
                  message.content.trim().length > 0 &&
                  (message.suggestedQuestions || []).length > 0 && (
                    <div className="px-4 pb-3">
                      <SuggestionChips
                        title={t('suggestionsFollowupLabel')}
                        suggestions={message.suggestedQuestions || []}
                        onSelect={(suggestion) => {
                          void handleSuggestionClick(suggestion);
                        }}
                        disabled={isLoading}
                      />
                    </div>
                  )}
              </Fragment>
            ))}

            {(streamingMessage || progressHint) && (
              <StreamingIndicator message={streamingMessage || progressHint} />
            )}
            {pendingClarification && (
              <div className="mx-4 mb-3 rounded-md border border-amber-500/40 bg-amber-500/10 p-3">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-amber-700">
                  {t('clarificationActionRequired')}
                </p>
                <p className="text-sm text-foreground">{pendingClarification.prompt}</p>
                {pendingClarification.questions.length > 0 && (
                  <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
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
              <div className="m-4 rounded-lg border border-destructive bg-destructive/10 p-4">
                <p className="mb-2 text-sm font-medium text-destructive">{t('error.title')}</p>
                <p className="mb-3 text-sm text-muted-foreground">{error.message}</p>
                <button
                  onClick={() => retryLastMessage()}
                  className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
                  type="button"
                >
                  <RefreshCw className="h-4 w-4" />
                  {t('error.retry')}
                </button>
              </div>
            )}

            <div aria-hidden="true" className="h-px" />
          </div>
        </CardContent>

        <Separator />
        <CardFooter className="sticky bottom-0 bg-background p-3">
          <form onSubmit={handleSubmit} className="flex w-full items-end gap-2">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('typePlaceholder')}
              className="min-h-[56px] w-full min-w-0 flex-1 resize-none rounded-md border bg-background px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-primary/40"
              rows={2}
              disabled={isLoading}
            />
            <Button
              type="submit"
              disabled={!input.trim() || isLoading}
              size="icon"
              aria-label={t('sendMessage')}
            >
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </CardFooter>
      </Card>

      <ChatWidget defaultOpen={false} zIndex={1300} />
    </main>
  );
}
