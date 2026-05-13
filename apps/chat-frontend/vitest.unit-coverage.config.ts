import { defineConfig, mergeConfig } from 'vitest/config';
import baseConfig from './vitest.config';

export default mergeConfig(
  baseConfig,
  defineConfig({
    test: {
      coverage: {
        include: [
          'src/app/components/KeyboardShortcutsHelp.tsx',
          'src/app/components/MessageFeedback.tsx',
          'src/app/components/SkipToContent.tsx',
          'src/app/components/ThemeToggle.tsx',
          'src/app/components/ui/card.tsx',
          'src/app/components/ui/input.tsx',
          'src/app/components/ui/label.tsx',
          'src/app/components/ui/skeleton.tsx',
          'src/app/components/ui/toggle.tsx',
          'src/app/components/ui/use-mobile.ts',
        ],
        thresholds: {
          lines: 98,
          functions: 98,
          branches: 98,
          statements: 98,
        },
      },
    },
  })
);