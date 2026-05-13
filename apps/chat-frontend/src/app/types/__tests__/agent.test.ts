/**
 * Tests for agent types and type guards
 *
 * Tests TypeScript type definitions and type guard functions.
 */

import { describe, it, expect } from 'vitest';
import {
  isThinkingEvent,
  isCompleteEvent,
  isClarificationEvent,
  isErrorEvent,
  type StreamEvent,
  type AgentSource,
  type AgentResponse,
  type AgentConfig,
} from '../agent';

describe('Type Guards', () => {
  describe('isThinkingEvent', () => {
    it('should return true for thinking events', () => {
      const event: StreamEvent = {
        type: 'thinking',
        message: 'Searching...',
      };

      expect(isThinkingEvent(event)).toBe(true);
    });

    it('should return false for non-thinking events', () => {
      const event: StreamEvent = {
        type: 'complete',
        answer: 'Done',
        sources: [],
      };

      expect(isThinkingEvent(event)).toBe(false);
    });

    it('should narrow type correctly', () => {
      const event: StreamEvent = {
        type: 'thinking',
        message: 'Test',
      };

      if (isThinkingEvent(event)) {
        // Should have access to message property
        expect(event.message).toBe('Test');
        // TypeScript should not error on toolName (optional)
        expect(event.toolName).toBeUndefined();
      }
    });
  });

  describe('isCompleteEvent', () => {
    it('should return true for complete events', () => {
      const event: StreamEvent = {
        type: 'complete',
        answer: 'Test answer',
        sources: [],
      };

      expect(isCompleteEvent(event)).toBe(true);
    });

    it('should return false for non-complete events', () => {
      const event: StreamEvent = {
        type: 'thinking',
        message: 'Processing...',
      };

      expect(isCompleteEvent(event)).toBe(false);
    });

    it('should narrow type correctly', () => {
      const event: StreamEvent = {
        type: 'complete',
        answer: 'Done',
        sources: [{ title: 'Test', url: 'http://example.com' }],
        thread_id: '123',
      };

      if (isCompleteEvent(event)) {
        expect(event.answer).toBe('Done');
        expect(event.sources).toHaveLength(1);
        expect(event.thread_id).toBe('123');
      }
    });
  });

  describe('isClarificationEvent', () => {
    it('should return true for clarification events', () => {
      const event: StreamEvent = {
        type: 'clarification',
        message: 'Can you provide more details?',
      };

      expect(isClarificationEvent(event)).toBe(true);
    });

    it('should return false for non-clarification events', () => {
      const event: StreamEvent = {
        type: 'complete',
        answer: 'Done',
        sources: [],
      };

      expect(isClarificationEvent(event)).toBe(false);
    });

    it('should narrow type correctly', () => {
      const event: StreamEvent = {
        type: 'clarification',
        message: 'Please clarify',
        suggestedQuestions: ['What do you mean?'],
      };

      if (isClarificationEvent(event)) {
        expect(event.message).toBe('Please clarify');
        expect(event.suggestedQuestions).toHaveLength(1);
      }
    });
  });

  describe('isErrorEvent', () => {
    it('should return true for error events', () => {
      const event: StreamEvent = {
        type: 'error',
        message: 'Something went wrong',
      };

      expect(isErrorEvent(event)).toBe(true);
    });

    it('should return false for non-error events', () => {
      const event: StreamEvent = {
        type: 'complete',
        answer: 'Done',
        sources: [],
      };

      expect(isErrorEvent(event)).toBe(false);
    });

    it('should narrow type correctly', () => {
      const event: StreamEvent = {
        type: 'error',
        message: 'Error occurred',
        code: 'SERVICE_ERROR',
      };

      if (isErrorEvent(event)) {
        expect(event.message).toBe('Error occurred');
        expect(event.code).toBe('SERVICE_ERROR');
      }
    });
  });
});

describe('Type Definitions', () => {
  describe('AgentSource', () => {
    it('should accept valid source objects', () => {
      const source: AgentSource = {
        title: 'Test Document',
        url: 'https://example.com/doc',
        type: 'document',
        isDownload: false,
        chunkIndex: 1,
        metadata: { content: 'Test content' },
        snippet: 'Test snippet',
      };

      expect(source.title).toBe('Test Document');
      expect(source.url).toBe('https://example.com/doc');
    });

    it('should accept minimal source objects', () => {
      const source: AgentSource = {
        title: 'Test',
        url: 'https://example.com',
      };

      expect(source).toBeDefined();
    });
  });

  describe('AgentResponse', () => {
    it('should accept valid response objects', () => {
      const response: AgentResponse = {
        answer: 'Test answer',
        sources: [],
        thread_id: 'thread-123',
        language: 'en',
        model: 'llama-3.1',
      };

      expect(response.answer).toBe('Test answer');
      expect(response.thread_id).toBe('thread-123');
    });

    it('should accept minimal response objects', () => {
      const response: AgentResponse = {
        answer: 'Test',
        sources: [],
      };

      expect(response).toBeDefined();
    });
  });

  describe('AgentConfig', () => {
    it('should accept valid config objects', () => {
      const config: AgentConfig = {
        providers: [
          {
            name: 'groq',
            models: ['llama-3.1-8b-instant'],
            default: true,
          },
        ],
        models: {
          groq: ['llama-3.1-8b-instant'],
        },
        defaultProvider: 'groq',
        defaultModel: 'llama-3.1-8b-instant',
      };

      expect(config.providers).toHaveLength(1);
      expect(config.defaultProvider).toBe('groq');
    });

    it('should accept minimal config objects', () => {
      const config: AgentConfig = {
        providers: [],
        models: {},
      };

      expect(config).toBeDefined();
    });
  });

  describe('StreamEvent discriminated union', () => {
    it('should enforce correct properties for each event type', () => {
      // Thinking event requires message
      const thinkingEvent: StreamEvent = {
        type: 'thinking',
        message: 'Processing...',
      };

      // Complete event requires answer and sources
      const completeEvent: StreamEvent = {
        type: 'complete',
        answer: 'Done',
        sources: [],
      };

      // Clarification event requires message
      const clarificationEvent: StreamEvent = {
        type: 'clarification',
        message: 'Please clarify',
      };

      // Error event requires message
      const errorEvent: StreamEvent = {
        type: 'error',
        message: 'Error occurred',
      };

      expect(thinkingEvent.type).toBe('thinking');
      expect(completeEvent.type).toBe('complete');
      expect(clarificationEvent.type).toBe('clarification');
      expect(errorEvent.type).toBe('error');
    });
  });
});
