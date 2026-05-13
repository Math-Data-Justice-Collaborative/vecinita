import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import {
  buildApiKeyUser,
  clearStoredApiKeySession,
  readStoredApiKeySession,
  storeApiKeySession,
  validateApiKey,
  type ApiKeySession,
  type ApiKeyUser,
} from './apiKeyAuth';

interface AuthContextValue {
  user: ApiKeyUser | null;
  session: ApiKeySession | null;
  loading: boolean;
  signIn: (apiKey: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<ApiKeySession | null>(null);
  const [user, setUser] = useState<ApiKeyUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const activeSession = readStoredApiKeySession();
    setSession(activeSession);
    setUser(activeSession ? buildApiKeyUser(activeSession) : null);
    setLoading(false);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      session,
      loading,
      signIn: async (apiKey) => {
        await validateApiKey(apiKey);
        const nextSession = storeApiKeySession(apiKey);
        setSession(nextSession);
        setUser(buildApiKeyUser(nextSession));
      },
      signOut: async () => {
        clearStoredApiKeySession();
        setSession(null);
        setUser(null);
      },
    }),
    [loading, session, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
