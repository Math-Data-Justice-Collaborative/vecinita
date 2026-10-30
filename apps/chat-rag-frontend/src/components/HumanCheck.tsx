import { useEffect, useRef, useState } from "react";
import { t } from "vecinita-frontend-i18n";
import { verifyHuman } from "../api/human";
import { useLocale } from "../hooks/useLocale";

const TURNSTILE_SCRIPT_SRC =
  "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

type TurnstileRenderOptions = {
  sitekey: string;
  language: string;
  callback: (token: string) => void;
  "error-callback": () => void;
  "expired-callback": () => void;
};

type TurnstileApi = {
  render: (el: HTMLElement, options: TurnstileRenderOptions) => string;
  remove: (widgetId: string) => void;
  reset: (widgetId: string) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

let scriptPromise: Promise<TurnstileApi> | null = null;

function loadTurnstile(): Promise<TurnstileApi> {
  if (window.turnstile) {
    return Promise.resolve(window.turnstile);
  }
  scriptPromise ??= new Promise<TurnstileApi>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = TURNSTILE_SCRIPT_SRC;
    script.async = true;
    script.onload = () => {
      if (window.turnstile) {
        resolve(window.turnstile);
      } else {
        reject(new Error("Turnstile unavailable"));
      }
    };
    script.onerror = () => {
      scriptPromise = null;
      reject(new Error("Turnstile script failed to load"));
    };
    document.head.appendChild(script);
  });
  return scriptPromise;
}

type Status = "loading" | "ready" | "verifying" | "failed" | "unavailable";

/** F-HUMAN: Turnstile "are you human?" widget shown before the first ask. */
export function HumanCheck({
  baseUrl,
  siteKey,
  onVerified,
}: {
  baseUrl: string;
  siteKey: string;
  onVerified: () => void;
}) {
  const { locale } = useLocale();
  const containerRef = useRef<HTMLDivElement>(null);
  const onVerifiedRef = useRef(onVerified);
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    onVerifiedRef.current = onVerified;
  }, [onVerified]);

  useEffect(() => {
    let cancelled = false;
    let widgetId: string | null = null;
    let api: TurnstileApi | null = null;

    loadTurnstile()
      .then((loaded) => {
        if (cancelled || !containerRef.current) {
          return;
        }
        api = loaded;
        widgetId = loaded.render(containerRef.current, {
          sitekey: siteKey,
          language: locale,
          callback: (token) => {
            setStatus("verifying");
            void verifyHuman(baseUrl, token).then((ok) => {
              if (cancelled) {
                return;
              }
              if (ok) {
                onVerifiedRef.current();
              } else {
                setStatus("failed");
                if (widgetId) {
                  loaded.reset(widgetId);
                }
              }
            });
          },
          "error-callback": () => {
            setStatus("failed");
          },
          "expired-callback": () => {
            setStatus("ready");
          },
        });
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) {
          setStatus("unavailable");
        }
      });

    return () => {
      cancelled = true;
      if (api && widgetId) {
        api.remove(widgetId);
      }
    };
  }, [baseUrl, siteKey, locale]);

  return (
    <div
      className="human-check"
      role="region"
      aria-label={t(locale, "chat.humanCheck.label")}
      data-testid="human-check"
    >
      <p className="human-check-prompt">
        {t(locale, "chat.humanCheck.prompt")}
      </p>
      <div ref={containerRef} className="human-check-widget" />
      {status === "verifying" ? (
        <p className="human-check-status" role="status">
          {t(locale, "chat.humanCheck.verifying")}
        </p>
      ) : null}
      {status === "failed" ? (
        <p className="human-check-status" role="alert">
          {t(locale, "chat.humanCheck.failed")}
        </p>
      ) : null}
      {status === "unavailable" ? (
        <p className="human-check-status" role="alert">
          {t(locale, "chat.humanCheck.unavailable")}
        </p>
      ) : null}
    </div>
  );
}
