import { useEffect, type ReactNode } from "react";

import {
  PlaygroundModelDownloadContext,
  usePlaygroundModelDownloadState,
} from "./playground-model-download-context";

export function PlaygroundModelDownloadProvider({
  children,
}: {
  children: ReactNode;
}) {
  const { clearDownloadPoll, ...value } = usePlaygroundModelDownloadState();

  useEffect(() => {
    return () => {
      clearDownloadPoll();
    };
  }, [clearDownloadPoll]);

  return (
    <PlaygroundModelDownloadContext.Provider value={value}>
      {children}
    </PlaygroundModelDownloadContext.Provider>
  );
}
