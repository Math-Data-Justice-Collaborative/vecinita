/**
 * Tests for component exports
 *
 * Ensures all components are properly exported from index.ts
 */

import { describe, it, expect } from 'vitest';
import * as Components from '../index';

describe('Component Exports', () => {
  it('should export ChatWidget', () => {
    expect(Components.ChatWidget).toBeDefined();
  });

  it('should export ChatMessage', () => {
    expect(Components.ChatMessage).toBeDefined();
  });

  it('should export ThemeToggle', () => {
    expect(Components.ThemeToggle).toBeDefined();
  });

  it('should export LanguageSelector', () => {
    expect(Components.LanguageSelector).toBeDefined();
  });

  it('should export AccessibilityPanel', () => {
    expect(Components.AccessibilityPanel).toBeDefined();
  });

  it('should export KeyboardShortcutsHelp', () => {
    expect(Components.KeyboardShortcutsHelp).toBeDefined();
  });

  it('should export SourceCard', () => {
    expect(Components.SourceCard).toBeDefined();
  });

  it('should export MessageFeedback', () => {
    expect(Components.MessageFeedback).toBeDefined();
  });

  it('should export SkipToContent', () => {
    expect(Components.SkipToContent).toBeDefined();
  });

  it('should export StreamingIndicator', () => {
    expect(Components.StreamingIndicator).toBeDefined();
  });

  it('should export TypingIndicator', () => {
    expect(Components.TypingIndicator).toBeDefined();
  });

  it('should have correct number of exports', () => {
    const exportedKeys = Object.keys(Components);

    // Should have all components (11) plus default export if any
    expect(exportedKeys.length).toBeGreaterThanOrEqual(11);
  });
});
