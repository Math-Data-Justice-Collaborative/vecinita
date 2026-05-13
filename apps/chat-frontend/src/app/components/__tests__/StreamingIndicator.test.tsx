/**
 * Tests for StreamingIndicator component
 *
 * Tests visual indicators for agent thinking/processing states.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StreamingIndicator, TypingIndicator } from '../StreamingIndicator';
import { LanguageProvider } from '../../context/LanguageContext';

// Mock localStorage with English as default
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

beforeEach(() => {
  localStorageMock.clear();
});

const LanguageWrapper = ({ children }: { children: React.ReactNode }) => (
  <LanguageProvider>{children}</LanguageProvider>
);

describe('StreamingIndicator', () => {
  it('should render with default message', () => {
    render(
      <LanguageWrapper>
        <StreamingIndicator />
      </LanguageWrapper>
    );

    expect(screen.getByText('Assistant is thinking...')).toBeInTheDocument();
  });

  it('should render with custom message', () => {
    render(
      <LanguageWrapper>
        <StreamingIndicator message="Searching documents..." />
      </LanguageWrapper>
    );

    expect(screen.getByText('Searching documents...')).toBeInTheDocument();
  });

  it('should have status role for accessibility', () => {
    render(
      <LanguageWrapper>
        <StreamingIndicator />
      </LanguageWrapper>
    );

    const indicator = screen.getByRole('status');
    expect(indicator).toBeInTheDocument();
  });

  it('should have aria-live attribute', () => {
    render(
      <LanguageWrapper>
        <StreamingIndicator />
      </LanguageWrapper>
    );

    const indicator = screen.getByRole('status');
    expect(indicator).toHaveAttribute('aria-live', 'polite');
  });

  it('should expose a stable test id and accessible label', () => {
    render(
      <LanguageWrapper>
        <StreamingIndicator />
      </LanguageWrapper>
    );

    const indicator = screen.getByTestId('streaming-indicator');
    expect(indicator).toHaveAttribute('role', 'status');
    expect(indicator).toHaveAttribute('aria-label', 'Assistant is thinking...');
  });

  it('should apply custom className', () => {
    const { container } = render(
      <LanguageWrapper>
        <StreamingIndicator className="custom-class" />
      </LanguageWrapper>
    );

    const indicator = container.querySelector('.custom-class');
    expect(indicator).toBeInTheDocument();
  });

  it('should show loading animation icon', () => {
    const { container } = render(
      <LanguageWrapper>
        <StreamingIndicator />
      </LanguageWrapper>
    );

    // Check for animation class
    const loader = container.querySelector('.animate-spin');
    expect(loader).toBeInTheDocument();
  });

  it('should not show custom message if not provided', () => {
    render(
      <LanguageWrapper>
        <StreamingIndicator />
      </LanguageWrapper>
    );

    // Should only have the default thinking message
    const messages = screen.queryAllByText(/searching/i);
    expect(messages).toHaveLength(0);
  });
});

describe('TypingIndicator', () => {
  it('should render three dots', () => {
    const { container } = render(<TypingIndicator />);

    const dots = container.querySelectorAll('.animate-bounce');
    expect(dots).toHaveLength(3);
  });

  it('should have status role', () => {
    render(<TypingIndicator />);

    const indicator = screen.getByRole('status');
    expect(indicator).toBeInTheDocument();
  });

  it('should have aria-label', () => {
    render(<TypingIndicator />);

    const indicator = screen.getByRole('status');
    expect(indicator).toHaveAttribute('aria-label', 'Typing');
  });

  it('should apply custom className', () => {
    const { container } = render(<TypingIndicator className="custom-class" />);

    const indicator = container.querySelector('.custom-class');
    expect(indicator).toBeInTheDocument();
  });

  it('should have staggered animation delays', () => {
    const { container } = render(<TypingIndicator />);

    const dots = container.querySelectorAll('.animate-bounce');

    expect(dots[0]).toHaveStyle({ animationDelay: '0ms' });
    expect(dots[1]).toHaveStyle({ animationDelay: '150ms' });
    expect(dots[2]).toHaveStyle({ animationDelay: '300ms' });
  });
});
