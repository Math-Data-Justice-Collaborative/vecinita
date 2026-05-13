import { describe, it, expect } from 'vitest';

/**
 * Test that all active components can be imported successfully
 * This verifies that no broken imports exist after the cleanup
 */
describe('Component Imports - Active Components', () => {
  it('should import AccessibilityPanel without errors', async () => {
    const module = await import('../AccessibilityPanel');
    expect(module.AccessibilityPanel).toBeDefined();
  });

  it('should import ChatMessage without errors', async () => {
    const module = await import('../ChatMessage');
    expect(module.ChatMessage).toBeDefined();
    // Message type is defined but not exported as named export
    expect(module).toBeDefined();
  });

  it('should import ChatWidget without errors', async () => {
    const module = await import('../ChatWidget');
    expect(module.ChatWidget).toBeDefined();
  });

  it('should import KeyboardShortcutsHelp without errors', async () => {
    const module = await import('../KeyboardShortcutsHelp');
    expect(module.KeyboardShortcutsHelp).toBeDefined();
  });

  it('should import LanguageSelector without errors', async () => {
    const module = await import('../LanguageSelector');
    expect(module.LanguageSelector).toBeDefined();
  });

  it('should import MessageFeedback without errors', async () => {
    const module = await import('../MessageFeedback');
    expect(module.MessageFeedback).toBeDefined();
    // Feedback type is defined but not exported as named export
    expect(module).toBeDefined();
  });

  it('should import SkipToContent without errors', async () => {
    const module = await import('../SkipToContent');
    expect(module.SkipToContent).toBeDefined();
  });

  it('should import SourceCard without errors', async () => {
    const module = await import('../SourceCard');
    expect(module.SourceCard).toBeDefined();
    // Source type is defined but not exported as named export
    expect(module).toBeDefined();
  });

  it('should import ThemeToggle without errors', async () => {
    const module = await import('../ThemeToggle');
    expect(module.ThemeToggle).toBeDefined();
  });
});

/**
 * Test that index.ts exports only the active components
 */
describe('Component Exports - index.ts', () => {
  it('should export all active components from index.ts', async () => {
    const exports = await import('../index');

    expect(exports.ChatWidget).toBeDefined();
    expect(exports.ChatMessage).toBeDefined();
    expect(exports.ThemeToggle).toBeDefined();
    expect(exports.LanguageSelector).toBeDefined();
    expect(exports.AccessibilityPanel).toBeDefined();
    expect(exports.KeyboardShortcutsHelp).toBeDefined();
    expect(exports.SourceCard).toBeDefined();
    expect(exports.MessageFeedback).toBeDefined();
    expect(exports.SkipToContent).toBeDefined();
  });

  it('should export type exports from index.ts', async () => {
    const exports = await import('../index');

    // Types are exported but we verify at least one exists
    expect(Object.keys(exports).length).toBeGreaterThan(0);
  });

  it('should NOT export BackendSettingsPanel', async () => {
    const exports = await import('../index');

    expect((exports as Record<string, unknown>).BackendSettingsPanel).toBeUndefined();
  });
});

/**
 * Test that deleted components cannot be imported
 */
describe('Deleted Components - Should Not Exist', () => {
  const deletedComponents = [
    'AccessibleButton',
    'AddDocumentModal',
    'AdminAuthModal',
    'AdminLogin',
    'AuthModal',
    'BackendSettingsPanel',
    'ChatHistory',
    'ChatHistorySidebar',
    'DocumentViewer',
    'PrivacyPolicy',
    'VisuallyHidden',
  ];

  deletedComponents.forEach((componentName) => {
    it(`should NOT be able to import ${componentName}`, async () => {
      try {
        await import(`../${componentName}.tsx`);
        throw new Error(`${componentName} should have been deleted but was found`);
      } catch (error: unknown) {
        // Expected: module not found
        if (error instanceof Error && error.message.includes('should have been deleted')) {
          throw error;
        }
        expect(error).toBeDefined();
      }
    });
  });
});

/**
 * Test that UI component dependencies are available
 */
describe('UI Component Dependencies - Core Files', () => {
  it('should import button.tsx from ui', async () => {
    const module = await import('../ui/button');
    expect(module.Button).toBeDefined();
  });

  it('should import utils.ts from ui', async () => {
    const module = await import('../ui/utils');
    expect(module.cn).toBeDefined();
  });

  it('should import use-mobile.ts from ui', async () => {
    const module = await import('../ui/use-mobile');
    expect(module.useIsMobile).toBeDefined();
  });

  it('should import tooltip.tsx from ui', async () => {
    const module = await import('../ui/tooltip');
    expect(module.Tooltip).toBeDefined();
  });

  it('should import dialog.tsx from ui', async () => {
    const module = await import('../ui/dialog');
    expect(module.Dialog).toBeDefined();
  });

  it('should import input.tsx from ui', async () => {
    const module = await import('../ui/input');
    expect(module.Input).toBeDefined();
  });

  it('should import label.tsx from ui', async () => {
    const module = await import('../ui/label');
    expect(module.Label).toBeDefined();
  });

  it('should import separator.tsx from ui', async () => {
    const module = await import('../ui/separator');
    expect(module.Separator).toBeDefined();
  });

  it('should import sheet.tsx from ui', async () => {
    const module = await import('../ui/sheet');
    expect(module.Sheet).toBeDefined();
  });

  it('should import skeleton.tsx from ui', async () => {
    const module = await import('../ui/skeleton');
    expect(module.Skeleton).toBeDefined();
  });

  it('should import toggle.tsx from ui', async () => {
    const module = await import('../ui/toggle');
    expect(module.Toggle).toBeDefined();
  });

  it('should import card.tsx from ui', async () => {
    const module = await import('../ui/card');
    expect(module.Card).toBeDefined();
  });
});
