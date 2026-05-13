import { Button } from './ui/button';

interface SuggestionChipsProps {
  title: string;
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  disabled?: boolean;
  compact?: boolean;
}

export function SuggestionChips({
  title,
  suggestions,
  onSelect,
  disabled = false,
  compact = false,
}: SuggestionChipsProps): JSX.Element | null {
  if (!suggestions.length) {
    return null;
  }

  return (
    <div className={compact ? 'mt-2 space-y-2' : 'mt-3 space-y-2'}>
      <p
        className={
          compact
            ? 'text-[11px] font-medium text-muted-foreground'
            : 'text-xs font-medium text-muted-foreground'
        }
      >
        {title}
      </p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, index) => (
          <Button
            key={`${index}-${suggestion}`}
            type="button"
            variant="outline"
            size={compact ? 'sm' : 'default'}
            className="max-w-full rounded-full whitespace-normal text-left"
            disabled={disabled}
            onClick={() => onSelect(suggestion)}
            aria-label={suggestion}
          >
            {suggestion}
          </Button>
        ))}
      </div>
    </div>
  );
}
