interface DocumentsOutageStateProps {
  message: string;
}

export function DocumentsOutageState({ message }: DocumentsOutageStateProps) {
  return (
    <main className="flex flex-1 items-center justify-center">
      <p className="text-destructive">{message}</p>
    </main>
  );
}
