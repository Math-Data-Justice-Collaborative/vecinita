/**
 * Conversation Storage Hook
 *
 * Manages local storage of conversation history with automatic 24-hour expiration.
 * Stores conversations in localStorage with thread-based keys.
 */

import { useEffect, useCallback, useMemo } from 'react';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  suggestedQuestions?: string[];
  sources?: Array<{
    title: string;
    url: string;
    snippet?: string;
  }>;
  timestamp: Date;
  feedback?: {
    rating: 'positive' | 'negative';
    comment?: string;
  };
}

interface StoredConversation {
  version?: number;
  messages: Message[];
  expiresAt: number;
  threadId: string;
  createdAt: number;
}

export const STORAGE_PREFIX = 'vecinita-thread-';
export const ACTIVE_THREAD_STORAGE_KEY = 'vecinita-active-thread';
const STORAGE_VERSION = 1;
const TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
const MAX_CONVERSATIONS = 20; // max stored threads
const MAX_MESSAGES_PER_THREAD = 100; // cap per thread to avoid quota overflow

export interface StorageSyncEvent {
  type: 'thread-updated' | 'thread-deleted' | 'active-thread-changed';
  threadId?: string;
}

/** Safe localStorage wrapper — never throws (private browsing, quota, etc.) */
const safeStorage = {
  get: (key: string): string | null => {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set: (key: string, value: string): boolean => {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch {
      return false;
    }
  },
  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  },
  keys: (): string[] => {
    try {
      return Array.from(
        { length: localStorage.length },
        (_, i) => localStorage.key(i) ?? ''
      ).filter(Boolean);
    } catch {
      return [];
    }
  },
};

function isConversationActive(data: StoredConversation): boolean {
  return Number(data.expiresAt) >= Date.now();
}

function parseStoredConversation(raw: string | null): StoredConversation | null {
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as StoredConversation;
    if (!parsed || typeof parsed !== 'object' || !parsed.threadId || !parsed.expiresAt) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function getStoredActiveThreadId(): string | null {
  const threadId = safeStorage.get(ACTIVE_THREAD_STORAGE_KEY);
  return threadId && threadId.trim() ? threadId : null;
}

export function setStoredActiveThreadId(threadId: string): void {
  safeStorage.set(ACTIVE_THREAD_STORAGE_KEY, threadId);
}

export function getLatestStoredThreadId(): string | null {
  const conversations: Array<{ threadId: string; createdAt: number }> = [];

  for (const key of safeStorage.keys()) {
    if (!key.startsWith(STORAGE_PREFIX)) {
      continue;
    }

    const parsed = parseStoredConversation(safeStorage.get(key));
    if (!parsed || !isConversationActive(parsed)) {
      continue;
    }

    conversations.push({ threadId: parsed.threadId, createdAt: Number(parsed.createdAt) || 0 });
  }

  conversations.sort((a, b) => b.createdAt - a.createdAt);
  return conversations[0]?.threadId || null;
}

/**
 * Custom hook for managing conversation storage with automatic cleanup.
 */
export function useConversationStorage(threadId: string) {
  const storageKey = `${STORAGE_PREFIX}${threadId}`;

  /**
   * Clear all expired conversations from localStorage.
   */
  const clearExpired = useCallback(() => {
    const now = Date.now();
    const keysToRemove: string[] = [];

    for (const key of safeStorage.keys()) {
      if (key.startsWith(STORAGE_PREFIX)) {
        const data = parseStoredConversation(safeStorage.get(key));
        if (!data || data.expiresAt < now) {
          keysToRemove.push(key);
        }
      }
    }

    keysToRemove.forEach((k) => safeStorage.remove(k));

    // Enforce MAX_CONVERSATIONS cap: evict oldest if over limit
    const allThreadKeys = safeStorage
      .keys()
      .filter((k) => k.startsWith(STORAGE_PREFIX))
      .map((k) => {
        const d = parseStoredConversation(safeStorage.get(k));
        return { key: k, createdAt: d?.createdAt ?? 0 };
      })
      .sort((a, b) => a.createdAt - b.createdAt); // oldest first

    if (allThreadKeys.length > MAX_CONVERSATIONS) {
      allThreadKeys
        .slice(0, allThreadKeys.length - MAX_CONVERSATIONS)
        .forEach(({ key }) => safeStorage.remove(key));
    }

    const activeThreadId = getStoredActiveThreadId();
    if (activeThreadId && !safeStorage.get(`${STORAGE_PREFIX}${activeThreadId}`)) {
      safeStorage.remove(ACTIVE_THREAD_STORAGE_KEY);
    }
  }, []);

  const saveMessagesForThread = useCallback(
    (targetThreadId: string, messages: Message[]) => {
      const targetStorageKey = `${STORAGE_PREFIX}${targetThreadId}`;
      const capped = messages.slice(-MAX_MESSAGES_PER_THREAD);
      const now = Date.now();
      const existing = parseStoredConversation(safeStorage.get(targetStorageKey));
      const conversation: StoredConversation = {
        version: STORAGE_VERSION,
        messages: capped,
        threadId: targetThreadId,
        createdAt: existing?.createdAt || now,
        expiresAt: now + TTL_MS,
      };

      const ok = safeStorage.set(targetStorageKey, JSON.stringify(conversation));
      if (!ok) {
        clearExpired();
        safeStorage.set(targetStorageKey, JSON.stringify(conversation));
      }
    },
    [clearExpired]
  );

  const loadMessagesForThread = useCallback((targetThreadId: string): Message[] | null => {
    const targetStorageKey = `${STORAGE_PREFIX}${targetThreadId}`;
    const data = parseStoredConversation(safeStorage.get(targetStorageKey));
    if (!data) {
      return null;
    }
    if (!isConversationActive(data)) {
      safeStorage.remove(targetStorageKey);
      return null;
    }
    return data.messages.map((msg) => ({
      ...msg,
      timestamp: new Date(msg.timestamp),
    }));
  }, []);

  const deleteThreadById = useCallback((targetThreadId: string) => {
    safeStorage.remove(`${STORAGE_PREFIX}${targetThreadId}`);
  }, []);

  /**
   * Save messages to localStorage with current timestamp and expiration.
   */
  const saveMessages = useCallback(
    (messages: Message[]) => {
      saveMessagesForThread(threadId, messages);
    },
    [threadId, saveMessagesForThread]
  );

  /**
   * Load messages from localStorage for the current thread.
   * Returns null if not found or expired.
   */
  const loadMessages = useCallback((): Message[] | null => {
    return loadMessagesForThread(threadId);
  }, [threadId, loadMessagesForThread]);

  /**
   * Delete the current thread from storage.
   */
  const deleteThread = useCallback(() => {
    deleteThreadById(threadId);
  }, [threadId, deleteThreadById]);

  /**
   * Get all stored thread IDs (non-expired).
   */
  const getAllThreadIds = useCallback((): string[] => {
    const now = Date.now();
    const threadIds: string[] = [];

    for (const key of safeStorage.keys()) {
      if (key.startsWith(STORAGE_PREFIX)) {
        const stored = safeStorage.get(key);
        if (stored) {
          const data = parseStoredConversation(stored);
          if (data && data.expiresAt >= now) {
            threadIds.push(data.threadId);
          }
        }
      }
    }
    return threadIds;
  }, []);

  /**
   * Get time until expiration for current thread in milliseconds.
   * Returns null if thread doesn't exist.
   */
  const getTimeRemaining = useCallback((): number | null => {
    const data = parseStoredConversation(safeStorage.get(storageKey));
    if (!data) {
      return null;
    }
    const remaining = data.expiresAt - Date.now();
    return remaining > 0 ? remaining : 0;
  }, [storageKey]);

  const getLatestThreadId = useCallback((): string | null => getLatestStoredThreadId(), []);

  const getActiveThreadId = useCallback((): string | null => getStoredActiveThreadId(), []);

  const setActiveThreadId = useCallback((newThreadId: string): void => {
    setStoredActiveThreadId(newThreadId);
  }, []);

  const subscribeToStorageEvents = useCallback(
    (listener: (event: StorageSyncEvent) => void): (() => void) => {
      const onStorage = (event: StorageEvent) => {
        if (!event.key) {
          return;
        }

        if (event.key === ACTIVE_THREAD_STORAGE_KEY) {
          listener({ type: 'active-thread-changed', threadId: event.newValue || undefined });
          return;
        }

        if (!event.key.startsWith(STORAGE_PREFIX)) {
          return;
        }

        const updatedThreadId = event.key.slice(STORAGE_PREFIX.length);
        if (!updatedThreadId) {
          return;
        }

        if (event.newValue === null) {
          listener({ type: 'thread-deleted', threadId: updatedThreadId });
          return;
        }

        listener({ type: 'thread-updated', threadId: updatedThreadId });
      };

      window.addEventListener('storage', onStorage);
      return () => {
        window.removeEventListener('storage', onStorage);
      };
    },
    []
  );

  // Run cleanup on mount
  useEffect(() => {
    clearExpired();
  }, [clearExpired]);

  // useMemo keeps the returned object reference stable across renders.
  // Without this, each render creates a new object, causing effects in
  // useAgentChat that depend on `storage` to re-run every render and
  // trigger a React infinite re-render loop.
  return useMemo(
    () => ({
      saveMessages,
      saveMessagesForThread,
      loadMessages,
      loadMessagesForThread,
      deleteThread,
      deleteThreadById,
      clearExpired,
      getAllThreadIds,
      getTimeRemaining,
      getLatestThreadId,
      getActiveThreadId,
      setActiveThreadId,
      subscribeToStorageEvents,
    }),
    [
      saveMessages,
      saveMessagesForThread,
      loadMessages,
      loadMessagesForThread,
      deleteThread,
      deleteThreadById,
      clearExpired,
      getAllThreadIds,
      getTimeRemaining,
      getLatestThreadId,
      getActiveThreadId,
      setActiveThreadId,
      subscribeToStorageEvents,
    ]
  );
}
