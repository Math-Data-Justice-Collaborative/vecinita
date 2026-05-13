import { ExternalLink } from 'lucide-react';
import { Card } from './ui/card';

export interface Source {
  title: string;
  url: string;
  snippet?: string;
}

interface SourceCardProps {
  source: Source;
  index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
  return (
    <Card className="overflow-hidden p-0 transition-colors hover:bg-accent">
      <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="group block p-2 sm:p-3"
        aria-label={`Source ${index + 1}: ${source.title}`}
      >
        <div className="flex items-start gap-1.5 sm:gap-2">
          <span className="mt-0.5 shrink-0 text-xs text-primary sm:text-sm" aria-hidden="true">
            [{index + 1}]
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-1.5 sm:gap-2">
              <h4 className="line-clamp-2 text-xs text-foreground transition-colors group-hover:text-primary sm:text-sm">
                {source.title}
              </h4>
              <ExternalLink
                className="mt-0.5 h-3 w-3 shrink-0 text-muted-foreground sm:h-4 sm:w-4"
                aria-hidden="true"
              />
            </div>
            {source.snippet && (
              <p className="mt-1 line-clamp-2 text-[10px] text-muted-foreground sm:text-xs">
                {source.snippet}
              </p>
            )}
          </div>
        </div>
      </a>
    </Card>
  );
}
