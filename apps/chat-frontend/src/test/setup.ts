import '@testing-library/jest-dom';
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers);

// Cleanup after each test case
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
});

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

const expectedConsoleNoise = [
  /Failed to fetch agent config/i,
  /useBackendSettings must be used within a BackendSettingsProvider/i,
  /useAuth must be used within an AuthProvider/i,
  /useLanguage must be used within a LanguageProvider/i,
  /The above error occurred in the <TestComponent> component/i,
];

const isErrorLike = (
  value: unknown
): value is { message?: unknown; stack?: unknown; name?: unknown } => {
  return typeof value === 'object' && value !== null && ('message' in value || 'stack' in value);
};

const formatConsoleArg = (arg: unknown): string => {
  if (typeof arg === 'string') {
    return arg;
  }

  if (arg instanceof Error) {
    return `${arg.name}: ${arg.message} ${arg.stack ?? ''}`;
  }

  if (isErrorLike(arg)) {
    const name = typeof arg.name === 'string' ? arg.name : 'Error';
    const message = typeof arg.message === 'string' ? arg.message : '';
    const stack = typeof arg.stack === 'string' ? arg.stack : '';
    const combined = `${name}: ${message} ${stack}`.trim();
    if (combined.length > 0) {
      return combined;
    }
  }

  try {
    return JSON.stringify(arg);
  } catch {
    return String(arg);
  }
};

const shouldSuppressConsoleMessage = (args: unknown[]): boolean => {
  const message = args.map((arg) => formatConsoleArg(arg)).join(' ');

  return expectedConsoleNoise.some((pattern) => pattern.test(message));
};

const shouldSuppressStderrChunk = (chunk: unknown): boolean => {
  const text =
    typeof chunk === 'string'
      ? chunk
      : chunk instanceof Uint8Array
        ? new TextDecoder().decode(chunk)
        : String(chunk);

  return expectedConsoleNoise.some((pattern) => pattern.test(text));
};

const originalConsoleError = console.error.bind(console);
vi.spyOn(console, 'error').mockImplementation((...args: unknown[]) => {
  if (shouldSuppressConsoleMessage(args)) {
    return;
  }
  originalConsoleError(...args);
});

const originalStderrWrite = process.stderr.write.bind(process.stderr);
vi.spyOn(process.stderr, 'write').mockImplementation(((...args: unknown[]) => {
  const [chunk] = args;
  if (shouldSuppressStderrChunk(chunk)) {
    return true;
  }

  return originalStderrWrite(...(args as Parameters<typeof process.stderr.write>));
}) as typeof process.stderr.write);
