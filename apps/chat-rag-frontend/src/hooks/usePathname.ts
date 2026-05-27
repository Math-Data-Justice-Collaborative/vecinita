import { useCallback, useEffect, useState } from "react";

/** Minimal SPA pathname hook without react-router (ADR-015 /corpus route). */
export function usePathname(): { pathname: string; navigate: (path: string) => void } {
  const [pathname, setPathname] = useState(() => window.location.pathname);

  useEffect(() => {
    const onPopState = () => { setPathname(window.location.pathname); };
    window.addEventListener("popstate", onPopState);
    return () => { window.removeEventListener("popstate", onPopState); };
  }, []);

  const navigate = useCallback((path: string) => {
    window.history.pushState({}, "", path);
    setPathname(path);
  }, []);

  return { pathname, navigate };
}
