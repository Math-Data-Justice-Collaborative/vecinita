import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ChatMessage } from '../ChatMessage';

const speakSpy = vi.fn();
let screenReaderEnabled = false;

vi.mock('../../context/LanguageContext', () => ({
  useLanguage: () => ({ t: (key: string) => (key === 'sources' ? 'Sources' : key) }),
}));

vi.mock('../../context/AccessibilityContext', () => ({
  useAccessibility: () => ({
    settings: { screenReader: screenReaderEnabled },
    speak: speakSpy,
  }),
}));

describe('ChatMessage source attribution', () => {
  beforeEach(() => {
    screenReaderEnabled = false;
    speakSpy.mockClear();
  });

  it('speaks assistant responses when screen reader mode is enabled', () => {
    screenReaderEnabled = true;

    render(
      <ChatMessage
        message={{
          id: 'assistant-a11y-1',
          role: 'assistant',
          content: 'A nearby clinic can help you find a doctor.',
          timestamp: new Date(),
          sources: [],
        }}
      />
    );

    expect(speakSpy).toHaveBeenCalledWith('A nearby clinic can help you find a doctor.');
  });

  it('exposes stable message selectors for e2e journeys', () => {
    render(
      <ChatMessage
        message={{
          id: 'assistant-selector-1',
          role: 'assistant',
          content: 'Selector contract check.',
          timestamp: new Date(),
          sources: [],
        }}
      />
    );

    const message = screen.getByTestId('chat-message');
    expect(message).toHaveAttribute('data-message-role', 'assistant');
    expect(message).toHaveAttribute('role', 'article');
  });

  it('marks user messages with the user role selector contract', () => {
    render(
      <ChatMessage
        message={{
          id: 'user-selector-1',
          role: 'user',
          content: 'I need a doctor nearby.',
          timestamp: new Date(),
          sources: [],
        }}
      />
    );

    const message = screen.getByTestId('chat-message');
    expect(message).toHaveAttribute('data-message-role', 'user');
    expect(screen.getByText('I need a doctor nearby.')).toBeInTheDocument();
    expect(message.querySelectorAll('a')).toHaveLength(0);
  });

  it('renders assistant markdown content safely', () => {
    render(
      <ChatMessage
        message={{
          id: 'assistant-md-1',
          role: 'assistant',
          content:
            '## Support Links\n\n- **Housing**\n- [Community Center](https://example.org/community)',
          timestamp: new Date(),
          sources: [],
        }}
      />
    );

    expect(screen.getByText('Support Links')).toBeInTheDocument();
    expect(screen.getByText('Housing')).toBeInTheDocument();
    const markdownLink = screen.getByRole('link', { name: 'Community Center' });
    expect(markdownLink).toHaveAttribute('href', 'https://example.org/community');
    expect(markdownLink).toHaveAttribute('target', '_blank');
    expect(markdownLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('renders wide markdown tables in a horizontally scrollable container', () => {
    render(
      <ChatMessage
        message={{
          id: 'assistant-table-1',
          role: 'assistant',
          content: '| Name | Details |\n| --- | --- |\n| River | Woonasquatucket Watershed |',
          timestamp: new Date(),
          sources: [],
        }}
      />
    );

    const table = screen.getByRole('table');
    expect(table.parentElement).toHaveClass('overflow-x-auto');
    expect(screen.getByText('Woonasquatucket Watershed')).toBeInTheDocument();
  });

  it('converts remote markdown images into external links instead of inline media', () => {
    render(
      <ChatMessage
        message={{
          id: 'assistant-image-remote-1',
          role: 'assistant',
          content: '![Flood map](https://example.org/flood-map.png)',
          timestamp: new Date(),
          sources: [],
        }}
      />
    );

    expect(screen.getByRole('link', { name: 'Flood map' })).toHaveAttribute(
      'href',
      'https://example.org/flood-map.png'
    );
    expect(screen.queryByRole('img', { name: 'Flood map' })).not.toBeInTheDocument();
  });

  it('strips raw html tags in assistant markdown rendering', () => {
    render(
      <ChatMessage
        message={{
          id: 'assistant-html-1',
          role: 'assistant',
          content: 'Safe text <script>alert("xss")</script> here',
          timestamp: new Date(),
          sources: [],
        }}
      />
    );

    expect(screen.getByText(/Safe text/)).toBeInTheDocument();
    expect(screen.queryByText(/<script>/i)).not.toBeInTheDocument();
  });

  it('shows fallback message when assistant content is empty', () => {
    render(
      <ChatMessage
        message={{
          id: 'assistant-empty-1',
          role: 'assistant',
          content: '   ',
          timestamp: new Date(),
          sources: [],
        }}
      />
    );

    expect(
      screen.getByText('I could not generate a response right now. Please try again.')
    ).toBeInTheDocument();
  });

  it('renders source cards linked to original URLs', () => {
    render(
      <ChatMessage
        message={{
          id: 'assistant-1',
          role: 'assistant',
          content: 'Here are resources with citations.',
          timestamp: new Date(),
          sources: [
            {
              title: 'Housing Benefits Guide',
              url: 'https://example.org/housing-guide',
              snippet: 'Official housing assistance guide',
            },
          ],
        }}
      />
    );

    expect(screen.getByText('Sources:')).toBeInTheDocument();

    const sourceLink = screen.getByRole('link', { name: /Source 1: Housing Benefits Guide/i });
    expect(sourceLink).toHaveAttribute('href', 'https://example.org/housing-guide');
    expect(screen.getByText('Official housing assistance guide')).toBeInTheDocument();
  });

  it('renders doctor-related markdown links and source cards together', () => {
    render(
      <ChatMessage
        message={{
          id: 'assistant-doctor-1',
          role: 'assistant',
          content:
            'Try the [Providence Community Health Center](https://clinic.example.org/providers) for help finding a doctor.',
          timestamp: new Date(),
          sources: [
            {
              title: 'Community Clinic Directory',
              url: 'https://clinic.example.org/directory',
              snippet: 'Directory of doctors and clinics near Providence.',
            },
          ],
        }}
      />
    );

    expect(
      screen.getByRole('link', { name: 'Providence Community Health Center' })
    ).toHaveAttribute('href', 'https://clinic.example.org/providers');
    expect(
      screen.getByRole('link', { name: /Source 1: Community Clinic Directory/i })
    ).toHaveAttribute('href', 'https://clinic.example.org/directory');
  });

  it('renders environmental reporting answer format with links and unverified placeholders', () => {
    render(
      <ChatMessage
        message={{
          id: 'assistant-env-1',
          role: 'assistant',
          content:
            'Based on the retrieved context, you can report environmental concerns in your neighborhood through VECINA (https://vecina.wrwc.org/).\n\nAdditionally, you can also report environmental concerns through the Woonasquatucket River Watershed Council (WRWC) ([1] https://wrwc.org/).\n\nThey have resources including neighborhood gardens ([2] [unverified link removed]).\n\nSources:\n[1]\nLink: https://wrwc.org/neighborhood-gardens/\n[2]\nVECINA',
          timestamp: new Date(),
          sources: [
            {
              title: 'WRWC Neighborhood Gardens',
              url: 'https://wrwc.org/neighborhood-gardens/',
              snippet: 'Neighborhood gardens resource page.',
            },
            {
              title: 'VECINA',
              url: 'https://vecina.wrwc.org/',
            },
          ],
        }}
      />
    );

    expect(screen.getByRole('link', { name: 'https://vecina.wrwc.org/' })).toHaveAttribute(
      'href',
      'https://vecina.wrwc.org/'
    );
    expect(screen.getByRole('link', { name: 'https://wrwc.org/' })).toHaveAttribute(
      'href',
      'https://wrwc.org/'
    );
    expect(
      screen.getByRole('link', { name: 'https://wrwc.org/neighborhood-gardens/' })
    ).toHaveAttribute('href', 'https://wrwc.org/neighborhood-gardens/');

    expect(screen.getByText(/unverified link removed/i)).toBeInTheDocument();

    expect(
      screen.getByRole('link', { name: /Source 1: WRWC Neighborhood Gardens/i })
    ).toHaveAttribute('href', 'https://wrwc.org/neighborhood-gardens/');
    expect(screen.getByRole('link', { name: /Source 2: VECINA/i })).toHaveAttribute(
      'href',
      'https://vecina.wrwc.org/'
    );
  });
});
