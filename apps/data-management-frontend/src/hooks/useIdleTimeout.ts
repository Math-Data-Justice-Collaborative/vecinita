import { useCallback, useEffect, useRef, useState } from "react";

import {
  idleTimeoutMinutes,
  idleWarningSeconds,
} from "@/config";

const ACTIVITY_EVENTS = [
  "mousemove",
  "keydown",
  "click",
  "scroll",
] as const;

const THROTTLE_MS = 1000;

export interface IdleTimeoutState {
  showWarning: boolean;
  secondsRemaining: number;
  staySignedIn: () => void;
  signOutNow: () => void;
}

export function useIdleTimeout(
  enabled: boolean,
  onTimeout: () => void | Promise<void>,
): IdleTimeoutState {
  const timeoutMs = idleTimeoutMinutes() * 60 * 1000;
  const warningMs = idleWarningSeconds() * 1000;
  const idleBeforeWarningMs = Math.max(timeoutMs - warningMs, 0);

  const [showWarning, setShowWarning] = useState(false);
  const [secondsRemaining, setSecondsRemaining] = useState(idleWarningSeconds());

  const warningTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const logoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastActivityRef = useRef(0);

  const clearTimers = useCallback(() => {
    if (warningTimerRef.current) {
      clearTimeout(warningTimerRef.current);
      warningTimerRef.current = null;
    }
    if (logoutTimerRef.current) {
      clearTimeout(logoutTimerRef.current);
      logoutTimerRef.current = null;
    }
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
  }, []);

  const onTimeoutRef = useRef(onTimeout);
  onTimeoutRef.current = onTimeout;

  const runTimeout = useCallback(() => {
    clearTimers();
    setShowWarning(false);
    void onTimeoutRef.current();
  }, [clearTimers]);

  const startWarningCountdown = useCallback(() => {
    setShowWarning(true);
    setSecondsRemaining(idleWarningSeconds());
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
    }
    countdownRef.current = setInterval(() => {
      setSecondsRemaining((prev) => {
        if (prev <= 1) {
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    logoutTimerRef.current = setTimeout(() => {
      runTimeout();
    }, warningMs);
  }, [runTimeout, warningMs]);

  const scheduleIdleCheck = useCallback(() => {
    clearTimers();
    setShowWarning(false);
    warningTimerRef.current = setTimeout(() => {
      startWarningCountdown();
    }, idleBeforeWarningMs);
  }, [clearTimers, idleBeforeWarningMs, startWarningCountdown]);

  const resetActivity = useCallback(() => {
    const now = Date.now();
    if (now - lastActivityRef.current < THROTTLE_MS) {
      return;
    }
    lastActivityRef.current = now;
    scheduleIdleCheck();
  }, [scheduleIdleCheck]);

  const staySignedIn = useCallback(() => {
    resetActivity();
  }, [resetActivity]);

  const signOutNow = useCallback(() => {
    runTimeout();
  }, [runTimeout]);

  useEffect(() => {
    if (!enabled) {
      clearTimers();
      setShowWarning(false);
      return undefined;
    }

    scheduleIdleCheck();

    for (const eventName of ACTIVITY_EVENTS) {
      window.addEventListener(eventName, resetActivity, { passive: true });
    }
    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        resetActivity();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      clearTimers();
      for (const eventName of ACTIVITY_EVENTS) {
        window.removeEventListener(eventName, resetActivity);
      }
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [clearTimers, enabled, resetActivity, scheduleIdleCheck]);

  return { showWarning, secondsRemaining, staySignedIn, signOutNow };
}
