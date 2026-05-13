const RAW_HTML_TAG_PATTERN = /<[^>]+>/g;
const MARKDOWN_IMAGE_PATTERN = /!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;

const REMOTE_PROTOCOLS = ['http://', 'https://'];

function isRemoteUrl(url: string): boolean {
  const lower = url.trim().toLowerCase();
  return REMOTE_PROTOCOLS.some((protocol) => lower.startsWith(protocol));
}

export function isSafeInlineImageUrl(url: string, origin?: string): boolean {
  const candidate = (url || '').trim();
  if (!candidate) {
    return false;
  }

  if (candidate.startsWith('data:image/')) {
    return true;
  }

  if (candidate.startsWith('/')) {
    return true;
  }

  if (candidate.startsWith('./') || candidate.startsWith('../')) {
    return true;
  }

  if (origin) {
    try {
      const parsed = new URL(candidate, origin);
      return parsed.origin === origin;
    } catch {
      return false;
    }
  }

  return false;
}

export function stripRawHtmlTags(markdown: string): string {
  return (markdown || '').replace(RAW_HTML_TAG_PATTERN, '');
}

export function rewriteRemoteMarkdownImagesToLinks(markdown: string): string {
  return (markdown || '').replace(MARKDOWN_IMAGE_PATTERN, (_full, altText: string, url: string) => {
    if (!isRemoteUrl(url)) {
      return `![${altText}](${url})`;
    }

    const label = (altText || url).trim();
    return `[${label}](${url})`;
  });
}

export function applyAssistantMarkdownPolicy(markdown: string, _origin?: string): string {
  const withoutHtml = stripRawHtmlTags(markdown);
  return rewriteRemoteMarkdownImagesToLinks(withoutHtml);
}
