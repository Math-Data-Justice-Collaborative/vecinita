import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { SourceCard } from '../SourceCard';

describe('SourceCard', () => {
  it('renders indexed source link with secure external attributes', () => {
    render(
      <SourceCard
        index={0}
        source={{
          title: 'Housing Benefits Guide',
          url: 'https://example.org/housing-guide',
        }}
      />
    );

    const link = screen.getByRole('link', { name: 'Source 1: Housing Benefits Guide' });
    expect(link).toHaveAttribute('href', 'https://example.org/housing-guide');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(screen.getByText('[1]')).toBeInTheDocument();
    expect(screen.getByText('Housing Benefits Guide')).toBeInTheDocument();
  });

  it('renders snippet when present', () => {
    render(
      <SourceCard
        index={1}
        source={{
          title: 'Community Support',
          url: 'https://example.org/community',
          snippet: 'Food and rental support details',
        }}
      />
    );

    expect(screen.getByText('[2]')).toBeInTheDocument();
    expect(screen.getByText('Food and rental support details')).toBeInTheDocument();
  });
});
