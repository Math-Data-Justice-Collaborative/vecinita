import { useCallback, useEffect, useState } from "react";

/** Fired after programmatic navigate so every hook instance stays in sync. */
const PATHNAME_SYNC_EVENT = "vecinita:pathname";

/** Minimal SPA pathname hook without react-router (ADR-015 /corpus route). */
export function usePathname(): {
  pathname: string;
  navigate: (path: string) => void;
} {
  const [pathname, setPathname] = useState(() => window.location.pathname);

  useEffect(() => {
    const sync = () => {
      setPathname(window.location.pathname);
    };
    window.addEventListener("popstate", sync);
    window.addEventListener(PATHNAME_SYNC_EVENT, sync);
    return () => {
      window.removeEventListener("popstate", sync);
      window.removeEventListener(PATHNAME_SYNC_EVENT, sync);
    };
  }, []);

  const navigate = useCallback((path: string) => {
    window.history.pushState({}, "", path);
    setPathname(path);
    window.dispatchEvent(new Event(PATHNAME_SYNC_EVENT));
  }, []);

  return { pathname, navigate };
}
