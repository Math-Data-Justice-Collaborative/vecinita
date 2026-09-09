import { useEffect, useState } from "react";

/** True after `ms` while `loading` stays true; resets when loading clears. */
export function useLoadTimeout(loading: boolean, ms = 15_000): boolean {
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    if (!loading) {
      setTimedOut(false);
      return;
    }
    const id = window.setTimeout(() => {
      setTimedOut(true);
    }, ms);
    return () => {
      window.clearTimeout(id);
    };
  }, [loading, ms]);

  return timedOut;
}
