/**
 * Tests for useConversationStorage hook
 *
 * Tests local storage management for conversation history with TTL.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import {
  useConversationStorage,
  ACTIVE_THREAD_STORAGE_KEY,
  type Message,
} from '../useConversationStorage';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    key: (index: number) => Object.keys(store)[index] || null,
    get length() {
      return Object.keys(store).length;
    },
  };
})();

Object.defineProperty(global, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

describe('useConversationStorage', () => {
  const threadId = 'test-thread-123';
  const sampleMessages: Message[] = [
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
      sources: [{ title: 'Test', url: 'https://example.com' }],
    },
  ];

  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('saveMessages', () => {
    it('should save messages to localStorage', () => {
      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.saveMessages(sampleMessages);
      });

      const stored = localStorage.getItem(`vecinita-thread-${threadId}`);
      expect(stored).toBeTruthy();

      const parsed = JSON.parse(stored!);
      expect(parsed.messages).toHaveLength(2);
      expect(parsed.threadId).toBe(threadId);
    });

    it('should set expiration 24 hours from now', () => {
      const now = Date.now();
      vi.setSystemTime(now);

      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.saveMessages(sampleMessages);
      });

      const stored = localStorage.getItem(`vecinita-thread-${threadId}`);
      const parsed = JSON.parse(stored!);

      const expectedExpiry = now + 24 * 60 * 60 * 1000;
      expect(parsed.expiresAt).toBe(expectedExpiry);
    });

    it('should handle quota exceeded error gracefully', () => {
      const storage = localStorage.setItem;
      vi.spyOn(localStorage, 'setItem').mockImplementationOnce(() => {
        const error = new Error('QuotaExceededError');
        error.name = 'QuotaExceededError';
        throw error;
      });

      const { result } = renderHook(() => useConversationStorage(threadId));

      // Should not throw
      expect(() => {
        act(() => {
          result.current.saveMessages(sampleMessages);
        });
      }).not.toThrow();

      localStorage.setItem = storage;
    });
  });

  describe('loadMessages', () => {
    it('should load messages from localStorage', () => {
      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.saveMessages(sampleMessages);
      });

      const loaded = result.current.loadMessages();

      expect(loaded).toHaveLength(2);
      expect(loaded![0].content).toBe('Hello');
      expect(loaded![1].content).toBe('Hi there!');
    });

    it('should return null for non-existent thread', () => {
      const { result } = renderHook(() => useConversationStorage('non-existent'));

      const loaded = result.current.loadMessages();

      expect(loaded).toBeNull();
    });

    it('should return null for expired thread', () => {
      const now = Date.now();
      vi.setSystemTime(now);

      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.saveMessages(sampleMessages);
      });

      // Move time forward 25 hours
      vi.setSystemTime(now + 25 * 60 * 60 * 1000);

      const loaded = result.current.loadMessages();

      expect(loaded).toBeNull();
    });

    it('should convert timestamp strings to Date objects', () => {
      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.saveMessages(sampleMessages);
      });

      const loaded = result.current.loadMessages();

      expect(loaded![0].timestamp).toBeInstanceOf(Date);
    });

    it('should handle corrupted data', () => {
      localStorage.setItem(`vecinita-thread-${threadId}`, 'invalid json');

      const { result } = renderHook(() => useConversationStorage(threadId));

      const loaded = result.current.loadMessages();

      expect(loaded).toBeNull();
    });
  });

  describe('deleteThread', () => {
    it('should delete thread from localStorage', () => {
      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.saveMessages(sampleMessages);
      });

      expect(localStorage.getItem(`vecinita-thread-${threadId}`)).toBeTruthy();

      act(() => {
        result.current.deleteThread();
      });

      expect(localStorage.getItem(`vecinita-thread-${threadId}`)).toBeNull();
    });
  });

  describe('clearExpired', () => {
    it('should remove expired threads', () => {
      const now = Date.now();
      vi.setSystemTime(now);

      // Create expired thread
      const expiredData = {
        messages: sampleMessages,
        threadId: 'expired-thread',
        createdAt: now - 30 * 60 * 60 * 1000,
        expiresAt: now - 1000, // Expired
      };
      localStorage.setItem('vecinita-thread-expired', JSON.stringify(expiredData));

      // Create valid thread
      const validData = {
        messages: sampleMessages,
        threadId: 'valid-thread',
        createdAt: now,
        expiresAt: now + 24 * 60 * 60 * 1000,
      };
      localStorage.setItem('vecinita-thread-valid', JSON.stringify(validData));

      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.clearExpired();
      });

      expect(localStorage.getItem('vecinita-thread-expired')).toBeNull();
      expect(localStorage.getItem('vecinita-thread-valid')).toBeTruthy();
    });

    it('should handle corrupted entries during cleanup', () => {
      localStorage.setItem('vecinita-thread-corrupted', 'invalid json');

      const { result } = renderHook(() => useConversationStorage(threadId));

      // Should not throw
      expect(() => {
        act(() => {
          result.current.clearExpired();
        });
      }).not.toThrow();

      // Corrupted entry should be removed
      expect(localStorage.getItem('vecinita-thread-corrupted')).toBeNull();
    });

    it('should run cleanup on hook mount', () => {
      const now = Date.now();
      vi.setSystemTime(now);

      // Create expired thread
      const expiredData = {
        messages: sampleMessages,
        threadId: 'expired',
        createdAt: now - 30 * 60 * 60 * 1000,
        expiresAt: now - 1000,
      };
      localStorage.setItem('vecinita-thread-expired', JSON.stringify(expiredData));

      renderHook(() => useConversationStorage('new-thread'));

      // Expired thread should be cleaned up automatically
      expect(localStorage.getItem('vecinita-thread-expired')).toBeNull();
    });
  });

  describe('getAllThreadIds', () => {
    it('should return all non-expired thread IDs', () => {
      const now = Date.now();
      vi.setSystemTime(now);

      // Create multiple threads
      ['thread1', 'thread2', 'thread3'].forEach((id) => {
        const data = {
          messages: [],
          threadId: id,
          createdAt: now,
          expiresAt: now + 24 * 60 * 60 * 1000,
        };
        localStorage.setItem(`vecinita-thread-${id}`, JSON.stringify(data));
      });

      const { result } = renderHook(() => useConversationStorage(threadId));

      const threadIds = result.current.getAllThreadIds();

      expect(threadIds).toHaveLength(3);
      expect(threadIds).toContain('thread1');
      expect(threadIds).toContain('thread2');
      expect(threadIds).toContain('thread3');
    });

    it('should exclude expired threads', () => {
      const now = Date.now();
      vi.setSystemTime(now);

      // Valid thread
      localStorage.setItem(
        'vecinita-thread-valid',
        JSON.stringify({
          threadId: 'valid',
          expiresAt: now + 1000,
          messages: [],
          createdAt: now,
        })
      );

      // Expired thread
      localStorage.setItem(
        'vecinita-thread-expired',
        JSON.stringify({
          threadId: 'expired',
          expiresAt: now - 1000,
          messages: [],
          createdAt: now,
        })
      );

      const { result } = renderHook(() => useConversationStorage(threadId));

      const threadIds = result.current.getAllThreadIds();

      expect(threadIds).toHaveLength(1);
      expect(threadIds).toContain('valid');
    });
  });

  describe('getTimeRemaining', () => {
    it('should return time until expiration', () => {
      const now = Date.now();
      vi.setSystemTime(now);

      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.saveMessages(sampleMessages);
      });

      const remaining = result.current.getTimeRemaining();

      expect(remaining).toBe(24 * 60 * 60 * 1000);
    });

    it('should return null for non-existent thread', () => {
      const { result } = renderHook(() => useConversationStorage('non-existent'));

      const remaining = result.current.getTimeRemaining();

      expect(remaining).toBeNull();
    });

    it('should return 0 for expired thread', () => {
      const now = Date.now();

      const expiredData = {
        messages: [],
        threadId,
        createdAt: now - 30 * 60 * 60 * 1000,
        expiresAt: now - 1000, // 1 second ago
      };
      localStorage.setItem(`vecinita-thread-${threadId}`, JSON.stringify(expiredData));

      const { result } = renderHook(() => useConversationStorage(threadId));

      const remaining = result.current.getTimeRemaining();

      // Expired threads should return 0 or null depending on implementation
      expect(remaining === 0 || remaining === null).toBe(true);
    });
  });

  describe('active thread and sync utilities', () => {
    it('should persist and read active thread id', () => {
      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.setActiveThreadId('active-thread-1');
      });

      expect(result.current.getActiveThreadId()).toBe('active-thread-1');
      expect(localStorage.getItem(ACTIVE_THREAD_STORAGE_KEY)).toBe('active-thread-1');
    });

    it('should return latest thread id by createdAt', () => {
      const now = Date.now();
      vi.setSystemTime(now);

      localStorage.setItem(
        'vecinita-thread-older',
        JSON.stringify({
          threadId: 'older',
          createdAt: now - 5_000,
          expiresAt: now + 60_000,
          messages: [],
        })
      );
      localStorage.setItem(
        'vecinita-thread-newer',
        JSON.stringify({
          threadId: 'newer',
          createdAt: now,
          expiresAt: now + 60_000,
          messages: [],
        })
      );

      const { result } = renderHook(() => useConversationStorage(threadId));
      expect(result.current.getLatestThreadId()).toBe('newer');
    });

    it('should save and load messages for a specific thread id', () => {
      const { result } = renderHook(() => useConversationStorage(threadId));

      act(() => {
        result.current.saveMessagesForThread('thread-special', sampleMessages);
      });

      const loaded = result.current.loadMessagesForThread('thread-special');
      expect(loaded).toHaveLength(2);
      expect(loaded?.[0].timestamp).toBeInstanceOf(Date);
    });

    it('should emit storage sync event for thread updates', () => {
      const { result } = renderHook(() => useConversationStorage(threadId));
      const listener = vi.fn();

      const unsubscribe = result.current.subscribeToStorageEvents(listener);
      window.dispatchEvent(
        new StorageEvent('storage', {
          key: 'vecinita-thread-thread-a',
          newValue: JSON.stringify({ threadId: 'thread-a' }),
          oldValue: null,
        })
      );

      expect(listener).toHaveBeenCalledWith({ type: 'thread-updated', threadId: 'thread-a' });
      unsubscribe();
    });

    it('should emit storage sync event for active-thread changes', () => {
      const { result } = renderHook(() => useConversationStorage(threadId));
      const listener = vi.fn();

      const unsubscribe = result.current.subscribeToStorageEvents(listener);
      window.dispatchEvent(
        new StorageEvent('storage', {
          key: ACTIVE_THREAD_STORAGE_KEY,
          newValue: 'thread-z',
          oldValue: 'thread-y',
        })
      );

      expect(listener).toHaveBeenCalledWith({
        type: 'active-thread-changed',
        threadId: 'thread-z',
      });
      unsubscribe();
    });
  });
});
