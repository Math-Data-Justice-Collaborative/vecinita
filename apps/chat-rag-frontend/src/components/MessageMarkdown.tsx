import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { citationHref } from "vecinita-frontend-ui";

type MessageMarkdownProps = {
  content: string;
};

function SafeLink({
  href,
  children,
}: {
  href?: string | undefined;
  children?: ReactNode;
}) {
  const safeHref = citationHref(href ?? null);
  if (safeHref === null) {
    return <span>{children}</span>;
  }
  return (
    <a href={safeHref} target="_blank" rel="noreferrer">
      {children}
    </a>
  );
}

export function MessageMarkdown({ content }: MessageMarkdownProps) {
  return (
    <div className="message-content markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => (
            <SafeLink href={href}>{children}</SafeLink>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
