import { cn } from "@/lib/utils";

type TruncatedSpanProps = {
  text: string;
  as?: "span";
  href?: undefined;
  className?: string | undefined;
  "data-testid"?: string | undefined;
};

type TruncatedAnchorProps = {
  text: string;
  as: "a";
  href: string;
  className?: string | undefined;
  "data-testid"?: string | undefined;
  target?: string | undefined;
  rel?: string | undefined;
};

export type TruncatedTextProps = TruncatedSpanProps | TruncatedAnchorProps;

/**
 * Clips long strings with ellipsis; full text via native `title` + `aria-label`.
 * No cookies / no storage — presentational only (EV-013 RD-181).
 */
export function TruncatedText(props: TruncatedTextProps) {
  const clipClass = cn(
    "max-w-full truncate text-foreground contrast-more:font-semibold",
    props.className,
  );

  if (props.as === "a") {
    return (
      <a
        href={props.href}
        title={props.text}
        aria-label={props.text}
        data-testid={props["data-testid"]}
        target={props.target}
        rel={props.rel}
        className={cn(
          clipClass,
          "inline-block text-primary underline-offset-4 hover:underline",
        )}
      >
        {props.text}
      </a>
    );
  }

  return (
    <span
      title={props.text}
      aria-label={props.text}
      data-testid={props["data-testid"]}
      className={cn(clipClass, "block")}
    >
      {props.text}
    </span>
  );
}
