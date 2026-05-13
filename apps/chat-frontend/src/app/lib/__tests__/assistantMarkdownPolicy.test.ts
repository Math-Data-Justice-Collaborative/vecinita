import { describe, expect, it } from 'vitest';

import {
  applyAssistantMarkdownPolicy,
  isSafeInlineImageUrl,
  rewriteRemoteMarkdownImagesToLinks,
  stripRawHtmlTags,
} from '../assistantMarkdownPolicy';
import { extractAssistantTextFromPayload } from '../assistantMessageNormalization';

describe('assistant markdown policy', () => {
  it('strips raw html tags from assistant markdown', () => {
    const content = 'Hello <script>alert(1)</script> world';
    expect(stripRawHtmlTags(content)).toBe('Hello alert(1) world');
  });

  it('rewrites remote markdown images into links', () => {
    const content = '![River photo](https://example.org/river.png)';
    expect(rewriteRemoteMarkdownImagesToLinks(content)).toBe(
      '[River photo](https://example.org/river.png)'
    );
  });

  it('preserves non-remote image markdown sources', () => {
    const content = '![Local](./assets/river.png)';
    expect(rewriteRemoteMarkdownImagesToLinks(content)).toContain('![Local](./assets/river.png)');
  });

  it('applies strip + remote image policy together', () => {
    const content = '<b>Notice</b>\n\n![Map](https://example.org/map.png)';
    const transformed = applyAssistantMarkdownPolicy(content);
    expect(transformed).toContain('Notice');
    expect(transformed).toContain('[Map](https://example.org/map.png)');
    expect(transformed).not.toContain('<b>');
  });

  it('allows only same-origin/data-url inline images', () => {
    expect(isSafeInlineImageUrl('data:image/png;base64,AAA')).toBe(true);
    expect(isSafeInlineImageUrl('/images/local.png')).toBe(true);
    expect(isSafeInlineImageUrl('https://cdn.example.org/image.png', 'https://vecina.org')).toBe(
      false
    );
    expect(isSafeInlineImageUrl('https://vecina.org/image.png', 'https://vecina.org')).toBe(true);
  });
});

describe('assistant message normalization', () => {
  it('extracts semantic answer from message.content payloads', () => {
    const payload = {
      model: 'llama3.2',
      message: { role: 'assistant', content: 'Structured response answer' },
    };
    expect(extractAssistantTextFromPayload(payload)).toBe('Structured response answer');
  });

  it('prefers answer field when present', () => {
    expect(
      extractAssistantTextFromPayload({ answer: 'Primary answer', message: { content: 'Ignored' } })
    ).toBe('Primary answer');
  });

  it('unwraps JSON-encoded answer strings that contain Ollama-style message content', () => {
    const wrapped = JSON.stringify({
      model: 'llama3.2',
      message: { role: 'assistant', content: 'User-visible body only.' },
    });
    expect(extractAssistantTextFromPayload({ answer: wrapped })).toBe('User-visible body only.');
  });

  it('reads top-level response for generate-style payloads', () => {
    expect(extractAssistantTextFromPayload({ response: '  From generate  ' })).toBe(
      'From generate'
    );
  });
});
