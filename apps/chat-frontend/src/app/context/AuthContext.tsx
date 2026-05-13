import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

const ADMIN_AUTH_ENABLED =
  (
    import.meta.env.VITE_ADMIN_AUTH_ENABLED ||
    import.meta.env.VITE_DEV_ADMIN_ENABLED ||
    'false'
  ).toLowerCase() === 'true';
const ADMIN_EMAIL = import.meta.env.VITE_ADMIN_EMAIL || import.meta.env.VITE_DEV_ADMIN_EMAIL || '';
const ADMIN_PASSWORD =
  import.meta.env.VITE_ADMIN_PASSWORD || import.meta.env.VITE_DEV_ADMIN_PASSWORD || '';
const ADMIN_TOKEN = import.meta.env.VITE_ADMIN_TOKEN || import.meta.env.VITE_DEV_ADMIN_TOKEN || '';
const ADMIN_STORAGE_KEY = 'vecinita-admin-session';

interface AdminUser {
  id: string;
  email: string;
  app_metadata: {
    role: 'admin';
  };
  user_metadata: {
    provider: 'direct-admin';
  };
  created_at: string;
}

interface AdminSession {
  email: string;
  token: string;
  createdAt: string;
}

function createAdminUser(email: string): AdminUser {
  const createdAt = new Date().toISOString();
  return {
    id: 'admin-local',
    email,
    app_metadata: { role: 'admin' },
    user_metadata: { provider: 'direct-admin' },
    created_at: createdAt,
  };
}

function readStoredSession(): AdminSession | null {
  try {
    const rawValue = localStorage.getItem(ADMIN_STORAGE_KEY);
    if (!rawValue) {
      return null;
    }

    const parsed = JSON.parse(rawValue) as Partial<AdminSession>;
    if (
      typeof parsed.email !== 'string' ||
      typeof parsed.token !== 'string' ||
      typeof parsed.createdAt !== 'string'
    ) {
      localStorage.removeItem(ADMIN_STORAGE_KEY);
      return null;
    }

    return {
      email: parsed.email,
      token: parsed.token,
      createdAt: parsed.createdAt,
    };
  } catch {
    localStorage.removeItem(ADMIN_STORAGE_KEY);
    return null;
  }
}

function buildSessionToken(): string {
  if (ADMIN_TOKEN.trim()) {
    return ADMIN_TOKEN.trim();
  }

  return 'local-admin-session';
}

interface AuthContextType {
  user: AdminUser | null;
  session: AdminSession | null;
  loading: boolean;
  isAdmin: boolean;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signUp: (email: string, password: string) => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  isAnonymous: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [session, setSession] = useState<AdminSession | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ADMIN_AUTH_ENABLED) {
      setLoading(false);
      return;
    }

    const activeSession = readStoredSession();
    if (activeSession && activeSession.email) {
      setSession(activeSession);
      setUser(createAdminUser(activeSession.email));
    } else {
      localStorage.removeItem(ADMIN_STORAGE_KEY);
      setSession(null);
      setUser(null);
    }

    setLoading(false);
  }, []);

  const signIn = async (email: string, password: string) => {
    if (!ADMIN_AUTH_ENABLED || !ADMIN_EMAIL || !ADMIN_PASSWORD) {
      return {
        error: new Error('Admin credentials are not configured for this frontend.'),
      };
    }

    if (
      email.trim().toLowerCase() !== ADMIN_EMAIL.trim().toLowerCase() ||
      password !== ADMIN_PASSWORD
    ) {
      return { error: new Error('Invalid admin credentials.') };
    }

    const nextSession: AdminSession = {
      email: ADMIN_EMAIL,
      token: buildSessionToken(),
      createdAt: new Date().toISOString(),
    };

    localStorage.setItem(ADMIN_STORAGE_KEY, JSON.stringify(nextSession));
    setSession(nextSession);
    setUser(createAdminUser(ADMIN_EMAIL));

    return { error: null };
  };

  const signUp = async (_email: string, _password: string) => {
    return {
      error: new Error(
        'Admin sign-up is disabled. Provision credentials through environment configuration.'
      ),
    };
  };

  const signOut = async () => {
    localStorage.removeItem(ADMIN_STORAGE_KEY);
    setUser(null);
    setSession(null);
  };

  const value = {
    user,
    session,
    loading,
    isAdmin: Boolean(session && user),
    signIn,
    signUp,
    signOut,
    isAnonymous: !user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
