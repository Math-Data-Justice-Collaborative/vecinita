import { describe, it, expect } from 'vitest';
import fs from 'fs';
import path from 'path';

/**
 * Tests to verify that deleted components are not referenced elsewhere
 * This is a file-system based test that scans the codebase for mentions of deleted components
 */
describe('Deleted Components - Codebase Verification', () => {
  const componentDir = path.resolve(__dirname, '..', '..');

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

  const deletedUIComponents = [
    'accordion',
    'alert-dialog',
    'alert',
    'aspect-ratio',
    'avatar',
    'badge',
    'breadcrumb',
    'calendar',
    'carousel',
    'chart',
    'checkbox',
    'collapsible',
    'command',
    'context-menu',
    'drawer',
    'dropdown-menu',
    'form',
    'hover-card',
    'input-otp',
    'menubar',
    'navigation-menu',
    'pagination',
    'popover',
    'progress',
    'radio-group',
    'resizable',
    'scroll-area',
    'select',
    'sidebar',
    'slider',
    'sonner',
    'switch',
    'table',
    'tabs',
    'textarea',
    'toggle-group',
  ];

  function scanFilesForReferences(dir: string, pattern: string, excludeDir?: string): boolean {
    try {
      const files = fs.readdirSync(dir, { withFileTypes: true });

      for (const file of files) {
        const fullPath = path.join(dir, file.name);

        // Skip excluded directories
        if (excludeDir && fullPath.includes(excludeDir)) {
          continue;
        }

        // Skip node_modules and build output
        if (file.name === 'node_modules' || file.name === 'dist' || file.name === '.git') {
          continue;
        }

        if (file.isDirectory()) {
          if (scanFilesForReferences(fullPath, pattern, excludeDir)) {
            return true;
          }
        } else if (
          file.name.endsWith('.ts') ||
          file.name.endsWith('.tsx') ||
          file.name.endsWith('.js') ||
          file.name.endsWith('.jsx')
        ) {
          // Skip test files for this verification (test files intentionally reference deleted components)
          if (file.name.includes('.test.')) {
            continue;
          }

          try {
            const content = fs.readFileSync(fullPath, 'utf-8');
            // Look for imports or component usage with more specificity
            // Match: import ... from './ui/pattern' or import ... from '@/...' patterns
            const importPatterns = [
              new RegExp(`import.*from\\s+['"].*/${pattern}['"]`, 'i'),
              new RegExp(`import.*from\\s+['"].*/${pattern}\\.tsx?['"]`, 'i'),
            ];

            if (importPatterns.some((regex) => regex.test(content))) {
              return true;
            }
          } catch {
            // Skip files that can't be read
          }
        }
      }

      return false;
    } catch {
      return false;
    }
  }

  describe('Deleted Component References', () => {
    deletedComponents.forEach((component) => {
      it(`should not reference ${component} in active code`, () => {
        const isReferenced = scanFilesForReferences(componentDir, component, '__tests__');
        expect(isReferenced).toBe(false);
      });
    });
  });

  describe('Deleted UI Component References', () => {
    deletedUIComponents.forEach((uiComponent) => {
      it(`should not reference ui/${uiComponent} in active code`, () => {
        const isReferenced = scanFilesForReferences(componentDir, uiComponent, '__tests__');
        expect(isReferenced).toBe(false);
      });
    });
  });

  describe('Component Files Should Exist', () => {
    const activeComponents = [
      'AccessibilityPanel.tsx',
      'ChatMessage.tsx',
      'ChatWidget.tsx',
      'KeyboardShortcutsHelp.tsx',
      'LanguageSelector.tsx',
      'MessageFeedback.tsx',
      'SkipToContent.tsx',
      'SourceCard.tsx',
      'ThemeToggle.tsx',
    ];

    activeComponents.forEach((component) => {
      it(`should have ${component} file`, () => {
        const filePath = path.join(componentDir, 'components', component);
        const exists = fs.existsSync(filePath);
        expect(exists).toBe(true);
      });
    });
  });

  describe('Deleted Component Files Should Not Exist', () => {
    deletedComponents.forEach((component) => {
      it(`should NOT have ${component}.tsx file`, () => {
        const filePath = path.join(componentDir, 'components', `${component}.tsx`);
        const exists = fs.existsSync(filePath);
        expect(exists).toBe(false);
      });
    });
  });

  describe('UI Component Files', () => {
    const remainingUIComponents = [
      'button.tsx',
      'card.tsx',
      'dialog.tsx',
      'input.tsx',
      'label.tsx',
      'separator.tsx',
      'sheet.tsx',
      'skeleton.tsx',
      'toggle.tsx',
      'tooltip.tsx',
      'use-mobile.ts',
      'utils.ts',
    ];

    remainingUIComponents.forEach((component) => {
      it(`should have ui/${component} file`, () => {
        const filePath = path.join(componentDir, 'components', 'ui', component);
        const exists = fs.existsSync(filePath);
        expect(exists).toBe(true);
      });
    });
  });

  describe('Deleted UI Component Files Should Not Exist', () => {
    deletedUIComponents.forEach((uiComponent) => {
      it(`should NOT have ui/${uiComponent}.tsx file`, () => {
        const filePath = path.join(componentDir, 'components', 'ui', `${uiComponent}.tsx`);
        const exists = fs.existsSync(filePath);
        expect(exists).toBe(false);
      });
    });
  });
});
