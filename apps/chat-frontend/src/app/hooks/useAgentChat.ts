/**
 * Agent Chat Hook
 *
 * Integrates agent service API calls with local conversation storage.
 * Handles streaming responses, message state, and thread management.
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { agentService, AgentServiceError } from '../services/agentService';
import {
  useConversationStorage,
  getStoredActiveThreadId,
  getLatestStoredThreadId,
  type Message,
} from './useConversationStorage';
import type { StreamEvent, AgentSource, AskQueryParams, AgentResponse } from '../types/agent';
import { getFallbackSuggestions, normalizeSuggestedQuestions } from '../lib/suggestions';
import {
  formatStageLabel,
  formatToolLabel,
  getAgentChatCopy,
  localizeStreamMessage,
} from '../lib/agentChatStream';
import { applyAssistantMarkdownPolicy } from '../lib/assistantMarkdownPolicy';
import { extractAssistantTextFromPayload } from '../lib/assistantMessageNormalization';

interface UseAgentChatOptions {
  initialThreadId?: string;
  language?: 'en' | 'es';
  provider?: string;
  model?: string;
  onError?: (error: AgentServiceError) => void;
  service?: {
    askStream: (params: AskQueryParams, onEvent: (event: StreamEvent) => void) => Promise<void>;
    ask: (params: AskQueryParams) => Promise<AgentResponse>;
  };
}

interface StreamProgressState {
  stage: string;
  percent: number;
  waiting: boolean;
  status: 'working' | 'waiting' | 'error';
}

interface PendingClarificationState {
  originalQuestion: string;
  prompt: string;
  questions: string[];
}

function emitAgentDebugEvent(scope: string, message: string, data?: unknown) {
  if (typeof window === 'undefined') {
    return;
  }

  window.dispatchEvent(
    new CustomEvent('vecinita:agent-debug', {
      detail: { scope, message, data },
    })
  );
}

export function useAgentChat(options: UseAgentChatOptions = {}) {
  const { initialThreadId, language, provider, model, onError, service } = options;
  const locale: 'en' | 'es' = language === 'es' ? 'es' : 'en';
  const copy = useMemo(() => getAgentChatCopy(locale), [locale]);

  const serviceClient = useMemo(() => service || agentService, [service]);
  const chatDebugEnabled =
    (import.meta as ImportMeta).env?.VITE_AGENT_DEBUG === 'true' ||
    (typeof window !== 'undefined' && window.localStorage.getItem('vecinita_debug_chat') === '1');

  const debugLog = useCallback(
    (message: string, data?: unknown) => {
      if (!chatDebugEnabled) {
        return;
      }

      emitAgentDebugEvent('useAgentChat', message, data);
    },
    [chatDebugEnabled]
  );
  const [threadId, setThreadId] = useState<string>(() => {
    if (initialThreadId) {
      return initialThreadId;
    }
    return getStoredActiveThreadId() || getLatestStoredThreadId() || uuidv4();
  });
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<string | null>(null);
  const [error, setError] = useState<AgentServiceError | null>(null);
  const [progressMessages, setProgressMessages] = useState<string[]>([]);
  const [pendingClarification, setPendingClarification] =
    useState<PendingClarificationState | null>(null);
  const [streamProgress, setStreamProgress] = useState<StreamProgressState>({
    stage: 'Starting',
    percent: 0,
    waiting: false,
    status: 'working',
  });

  const storage = useConversationStorage(threadId);
  const splashSuggestions = useMemo(() => getFallbackSuggestions(locale, 'splash'), [locale]);

  const appendProgressMessage = useCallback((message: string) => {
    const value = (message || '').trim();
    if (!value) {
      return;
    }
    setProgressMessages((current) => {
      const deduped = current[current.length - 1] === value ? current : [...current, value];
      return deduped.slice(-8);
    });
  }, []);

  const localizeMessage = useCallback(
    (message?: string) => localizeStreamMessage(locale, message),
    [locale]
  );

  // Keep one active-thread pointer so route changes/reloads restore the same conversation.
  useEffect(() => {
    storage.setActiveThreadId(threadId);
    debugLog('thread:active_set', { threadId });
  }, [threadId, storage, debugLog]);

  /**
   * Load conversation history from localStorage on mount or thread change.
   */
  useEffect(() => {
    const loadedMessages = storage.loadMessages();
    setMessages(loadedMessages || []);
    debugLog('thread:rehydrate', {
      threadId,
      restoredMessageCount: loadedMessages?.length || 0,
    });
  }, [storage, threadId, debugLog]);

  // Sync local in-memory state when another tab updates chat storage.
  useEffect(() => {
    return storage.subscribeToStorageEvents((event) => {
      if (event.type === 'active-thread-changed' && event.threadId && event.threadId !== threadId) {
        debugLog('storage:event_active_thread_changed', {
          fromThreadId: threadId,
          toThreadId: event.threadId,
        });
        setThreadId(event.threadId);
        return;
      }

      if (event.threadId !== threadId) {
        return;
      }

      if (event.type === 'thread-deleted') {
        debugLog('storage:event_thread_deleted', { threadId });
        setMessages([]);
        return;
      }

      const syncedMessages = storage.loadMessages() || [];
      debugLog('storage:event_thread_updated', {
        threadId,
        syncedMessageCount: syncedMessages.length,
      });
      setMessages(syncedMessages);
    });
  }, [storage, threadId, debugLog]);

  /**
   * Convert agent sources to message sources format.
   */
  const mapSources = (agentSources: AgentSource[]) => {
    return agentSources.map((source) => ({
      title: source.title,
      url: source.url,
      snippet: source.metadata?.content as string | undefined,
    }));
  };

  const resolveFollowUpSuggestions = useCallback(
    (rawSuggestions?: string[]) => {
      const normalized = normalizeSuggestedQuestions(rawSuggestions);
      if (normalized.length > 0) {
        return normalized;
      }
      return getFallbackSuggestions(locale, 'followup');
    },
    [locale]
  );

  /**
   * Send a message and get a streaming response.
   */
  const sendMessage = useCallback(
    async (question: string) => {
      if (!question.trim()) return;

      setIsLoading(true);
      setError(null);
      setStreamingMessage(copy.connecting);
      setProgressMessages([]);
      setPendingClarification(null);
      setStreamProgress({
        stage: 'Connecting',
        percent: 5,
        waiting: true,
        status: 'waiting',
      });
      appendProgressMessage(`⏳ ${copy.connecting}`);

      // Create and add user message immediately
      const userMessage: Message = {
        id: uuidv4(),
        role: 'user',
        content: question,
        timestamp: new Date(),
      };

      let workingMessages = [...messages, userMessage];
      setMessages(workingMessages);
      storage.saveMessagesForThread(threadId, workingMessages);

      const appendAssistantEventMessage = (content: string) => {
        const value = content.trim();
        if (!value) {
          return;
        }

        const eventMessage: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: value,
          timestamp: new Date(),
        };

        workingMessages = [...workingMessages, eventMessage];
        setMessages(workingMessages);
        storage.saveMessagesForThread(threadId, workingMessages);
      };

      const activeClarification = pendingClarification;
      const lastAssistantContext = [...messages]
        .reverse()
        .find((message) => message.role === 'assistant' && message.content?.trim())?.content;
      const requestParams: AskQueryParams = {
        question: activeClarification?.originalQuestion || question,
        thread_id: threadId,
        context_answer: lastAssistantContext,
        lang: language,
        provider,
        model,
        clarification_response: activeClarification ? question : undefined,
      };

      try {
        debugLog('sendMessage:start', {
          question,
          threadId,
          hasPendingClarification: Boolean(activeClarification),
        });
        let assistantContent = '';
        let assistantSources: AgentSource[] = [];
        let newThreadId = threadId;
        const latestToolResults = new Map<string, string>();
        let streamEventCount = 0;
        let sawCompleteEvent = false;
        let sawClarificationEvent = false;
        let assistantSuggestedQuestions: string[] = [];

        const updateProgressFromEvent = (event: {
          stage?: string;
          progress?: number;
          waiting?: boolean;
          status?: 'working' | 'waiting' | 'error';
        }) => {
          setStreamProgress((current) => {
            const nextPercent = Math.max(0, Math.min(100, event.progress ?? current.percent));
            const nextStage = formatStageLabel(event.stage) || current.stage;
            const nextWaiting = Boolean(event.waiting);
            const nextStatus = event.status || (nextWaiting ? 'waiting' : 'working');

            return {
              stage: nextStage,
              percent: nextPercent,
              waiting: nextWaiting,
              status: nextStatus,
            };
          });
        };

        // Stream response from agent
        await serviceClient.askStream(requestParams, (event: StreamEvent) => {
          streamEventCount += 1;
          debugLog('stream:event', { type: event.type, count: streamEventCount });
          switch (event.type) {
            case 'thinking':
              setStreamingMessage(localizeMessage(event.message));
              updateProgressFromEvent(event);
              appendProgressMessage(`• ${localizeMessage(event.message)}`);
              break;

            case 'token':
              // Accumulate tokens as they stream in
              assistantContent += event.content || '';
              // Update UI with streaming response
              setStreamingMessage(copy.generating);
              break;

            case 'source':
              // Add source as it's discovered
              if (event.url && event.title) {
                assistantSources.push({
                  url: event.url,
                  title: event.title,
                  type: event.source_type || 'document',
                } as AgentSource);
              }
              break;

            case 'complete':
              sawCompleteEvent = true;
              assistantContent = extractAssistantTextFromPayload({
                answer: event.answer,
              });
              assistantSources = event.sources || assistantSources;
              assistantSuggestedQuestions = resolveFollowUpSuggestions(
                event.suggestedQuestions || event.suggested_questions
              );
              setPendingClarification(null);
              if (event.thread_id) {
                newThreadId = event.thread_id;
              }
              debugLog('stream:complete', { metadata: event.metadata });
              setStreamingMessage(null);
              setStreamProgress({
                stage: 'Complete',
                percent: event.metadata?.progress ?? 100,
                waiting: false,
                status: 'working',
              });
              break;

            case 'clarification':
              // Handle clarification requests
              {
                sawClarificationEvent = true;
                const clarificationMessage =
                  localizeMessage(event.message) ||
                  (event.questions && event.questions.length > 0
                    ? event.questions.join(' ')
                    : 'Please provide more details so I can continue.');
                const clarificationQuestions = (event.questions || event.suggestedQuestions || [])
                  .filter((value): value is string => Boolean(value && value.trim()))
                  .slice(0, 3);

                const displayMessage =
                  clarificationQuestions.length > 0
                    ? `${copy.clarificationNeeded}:\n${clarificationMessage}\n\n${clarificationQuestions.map((item, idx) => `${idx + 1}. ${item}`).join('\n')}`
                    : `${copy.clarificationNeeded}: ${clarificationMessage}`;
                setStreamingMessage(displayMessage);
                appendProgressMessage(displayMessage);
                updateProgressFromEvent({
                  stage: event.stage || 'clarification',
                  progress: event.progress ?? 85,
                  waiting: true,
                  status: 'waiting',
                });
                setPendingClarification({
                  originalQuestion: activeClarification?.originalQuestion || question,
                  prompt: clarificationMessage,
                  questions: clarificationQuestions,
                });
                appendAssistantEventMessage(displayMessage);
              }
              break;

            case 'error':
              updateProgressFromEvent({
                stage: event.stage || 'error',
                progress: event.progress ?? 100,
                waiting: false,
                status: 'error',
              });
              throw new AgentServiceError(event.message, undefined, event.code);

            case 'tool_event': {
              setStreamingMessage(localizeMessage(event.message));
              updateProgressFromEvent(event);
              const localizedToolMessage = localizeMessage(event.message);
              if (event.phase === 'start') {
                appendProgressMessage(`⏳ ${localizedToolMessage}`);
              } else if (event.phase === 'result') {
                appendProgressMessage(`✅ ${localizedToolMessage}`);
              } else {
                appendProgressMessage(`⚠️ ${localizedToolMessage}`);
              }
              if (event.phase === 'result' && event.tool && event.message) {
                latestToolResults.set(event.tool, localizedToolMessage);
              }
              break;
            }
          }
        });

        if (!assistantContent.trim() && !sawClarificationEvent) {
          debugLog('stream:empty_response_fallback', {
            question,
            threadId,
            streamEventCount,
            sawCompleteEvent,
          });

          const fallbackResponse = await serviceClient.ask(requestParams);
          assistantContent = fallbackResponse.answer || '';
          assistantSources = fallbackResponse.sources || assistantSources;
          assistantSuggestedQuestions = resolveFollowUpSuggestions(
            fallbackResponse.suggested_questions
          );
          if (fallbackResponse.thread_id) {
            newThreadId = fallbackResponse.thread_id;
          }

          debugLog('fallback:non_stream_after_empty_stream', {
            question,
            threadId,
            fallbackHasAnswer: Boolean(assistantContent.trim()),
          });
        }

        if (!assistantContent.trim() && !sawClarificationEvent) {
          assistantContent = copy.emptyResponse;
          debugLog('empty_response:using_default_assistant_message', {
            question,
            threadId,
            streamEventCount,
          });
        }

        if (assistantContent.trim()) {
          assistantContent = applyAssistantMarkdownPolicy(
            assistantContent,
            typeof window !== 'undefined' ? window.location.origin : undefined
          );
        }

        if (latestToolResults.size > 0) {
          const toolSummary = Array.from(latestToolResults.entries())
            .map(([toolName, summary]) => `• ${formatToolLabel(toolName)}\n  ${summary}`)
            .join('\n');
          appendAssistantEventMessage(`${copy.toolSummaryTitle}\n────────────\n${toolSummary}`);
        }

        // Create assistant message when final answer exists
        let finalMessages = workingMessages;
        if (assistantContent.trim()) {
          const assistantMessage: Message = {
            id: uuidv4(),
            role: 'assistant',
            content: assistantContent,
            sources: mapSources(assistantSources),
            suggestedQuestions: assistantSuggestedQuestions,
            timestamp: new Date(),
          };
          finalMessages = [...finalMessages, assistantMessage];
          setMessages(finalMessages);
        }

        // Update thread ID if it changed and persist on the correct thread key.
        if (newThreadId !== threadId) {
          setThreadId(newThreadId);
        }
        storage.saveMessagesForThread(newThreadId, finalMessages);
        debugLog('sendMessage:success', {
          question,
          threadId,
          finalMessageCount: finalMessages.length,
        });
      } catch (err) {
        debugLog('sendMessage:stream_or_processing_error', {
          question,
          threadId,
          error: err instanceof Error ? err.message : 'unknown',
        });
        let agentError =
          err instanceof AgentServiceError ? err : new AgentServiceError(copy.unexpectedError);

        try {
          const fallbackResponse = await serviceClient.ask(requestParams);
          let fallbackMessages = workingMessages;

          const fallbackAnswer = (fallbackResponse.answer || '').trim();
          if (fallbackAnswer) {
            const normalizedFallbackAnswer = applyAssistantMarkdownPolicy(
              fallbackAnswer,
              typeof window !== 'undefined' ? window.location.origin : undefined
            );
            const fallbackAssistantMessage: Message = {
              id: uuidv4(),
              role: 'assistant',
              content: normalizedFallbackAnswer,
              sources: mapSources(fallbackResponse.sources || []),
              suggestedQuestions: resolveFollowUpSuggestions(fallbackResponse.suggested_questions),
              timestamp: new Date(),
            };
            fallbackMessages = [...fallbackMessages, fallbackAssistantMessage];
            setMessages(fallbackMessages);
          } else {
            const fallbackAssistantMessage: Message = {
              id: uuidv4(),
              role: 'assistant',
              content: copy.emptyResponse,
              timestamp: new Date(),
            };
            fallbackMessages = [...fallbackMessages, fallbackAssistantMessage];
            setMessages(fallbackMessages);
          }

          if (fallbackResponse.thread_id && fallbackResponse.thread_id !== threadId) {
            setThreadId(fallbackResponse.thread_id);
          }

          setError(null);
          storage.saveMessagesForThread(fallbackResponse.thread_id || threadId, fallbackMessages);
          debugLog('sendMessage:fallback_success', {
            question,
            threadId,
            fallbackMessageCount: fallbackMessages.length,
          });
          return;
        } catch (fallbackError) {
          debugLog('sendMessage:fallback_failed', {
            question,
            threadId,
            error: fallbackError instanceof Error ? fallbackError.message : 'unknown',
          });
          agentError =
            fallbackError instanceof AgentServiceError
              ? fallbackError
              : new AgentServiceError(copy.unexpectedError);
        }

        setError(agentError);
        if (onError) {
          onError(agentError);
        }

        // Add error message to chat
        const errorMessage: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: `${copy.encounteredErrorPrefix} ${agentError.message}`,
          timestamp: new Date(),
        };

        const finalMessages = [...workingMessages, errorMessage];
        setMessages(finalMessages);
        storage.saveMessagesForThread(threadId, finalMessages);
      } finally {
        setIsLoading(false);
        setStreamingMessage(null);
        setStreamProgress((current) => ({
          ...current,
          waiting: false,
          percent: current.status === 'error' ? current.percent : Math.max(current.percent, 100),
        }));
      }
    },
    [
      messages,
      threadId,
      storage,
      appendProgressMessage,
      localizeMessage,
      pendingClarification,
      language,
      provider,
      model,
      serviceClient,
      onError,
      debugLog,
      copy.clarificationNeeded,
      copy.connecting,
      copy.emptyResponse,
      copy.encounteredErrorPrefix,
      copy.generating,
      copy.toolSummaryTitle,
      copy.unexpectedError,
      resolveFollowUpSuggestions,
    ]
  );

  /**
   * Load an existing thread by ID.
   */
  const loadThread = useCallback(
    (newThreadId: string) => {
      setThreadId(newThreadId);
      storage.setActiveThreadId(newThreadId);
      debugLog('thread:manual_load', { newThreadId });
    },
    [storage, debugLog]
  );

  /**
   * Start a completely new conversation — new thread ID, clear messages.
   * Never calls any external service. Everything stays in localStorage.
   */
  const startNewConversation = useCallback(() => {
    storage.deleteThreadById(threadId);
    setMessages([]);
    const nextThreadId = uuidv4();
    setThreadId(nextThreadId);
    storage.setActiveThreadId(nextThreadId);
    debugLog('thread:new_conversation_started', {
      deletedThreadId: threadId,
      nextThreadId,
    });
    setError(null);
    setStreamingMessage(null);
    setPendingClarification(null);
  }, [storage, threadId, debugLog]);

  /**
   * Clear the current thread and start fresh.
   * Alias for startNewConversation for backward compat.
   */
  const clearThread = useCallback(() => {
    startNewConversation();
  }, [startNewConversation]);

  /**
   * Retry the last message (useful after errors).
   */
  const retryLastMessage = useCallback(() => {
    const lastUserMessage = [...messages].reverse().find((msg) => msg.role === 'user');

    if (lastUserMessage) {
      // Remove last assistant message if it was an error
      const filteredMessages = messages.slice(0, -1);
      setMessages(filteredMessages);
      storage.saveMessagesForThread(threadId, filteredMessages);

      // Resend the question
      sendMessage(lastUserMessage.content);
    }
  }, [messages, storage, sendMessage, threadId]);

  return {
    threadId,
    messages,
    isLoading,
    streamingMessage,
    error,
    progressMessages,
    streamProgress,
    pendingClarification,
    splashSuggestions,
    sendMessage,
    loadThread,
    clearThread,
    startNewConversation,
    retryLastMessage,
    getAllThreadIds: storage.getAllThreadIds,
    getTimeRemaining: storage.getTimeRemaining,
  };
}
