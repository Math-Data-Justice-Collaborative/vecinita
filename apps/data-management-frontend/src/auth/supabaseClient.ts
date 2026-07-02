import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as
  | string
  | undefined;

export const REMEMBER_STORAGE_KEY = "vecinita.auth.remember";

let client: SupabaseClient | null = null;
let clientRemember: boolean | null = null;
let clientVersion = 0;
const clientVersionListeners = new Set<() => void>();
let testClientInjected = false;

function notifyClientVersionChange(): void {
  clientVersion += 1;
  for (const listener of clientVersionListeners) {
    listener();
  }
}

/** Subscribe when the singleton is rebuilt (e.g. remember-me storage routing). */
export function subscribeSupabaseClientVersion(
  onChange: () => void,
): () => void {
  clientVersionListeners.add(onChange);
  return () => {
    clientVersionListeners.delete(onChange);
  };
}

export function getSupabaseClientVersion(): number {
  return clientVersion;
}

export type SupportedStorage = Pick<
  Storage,
  "getItem" | "setItem" | "removeItem"
>;

/** Route Supabase auth persistence to localStorage (remember) or sessionStorage. */
export function createRoutingStorage(remember: boolean): SupportedStorage {
  const storage = remember ? localStorage : sessionStorage;
  return {
    getItem: (key: string) => storage.getItem(key),
    setItem: (key: string, value: string) => {
      storage.setItem(key, value);
    },
    removeItem: (key: string) => {
      storage.removeItem(key);
    },
  };
}

export function readRememberPreference(): boolean {
  try {
    const raw = localStorage.getItem(REMEMBER_STORAGE_KEY);
    if (raw === "false") {
      return false;
    }
  } catch {
    return true;
  }
  return true;
}

export function persistRememberPreference(remember: boolean): void {
  try {
    localStorage.setItem(REMEMBER_STORAGE_KEY, remember ? "true" : "false");
  } catch {
    // Degrade silently — default routing storage still applies.
  }
}

function buildClient(remember: boolean): SupabaseClient {
  if (!supabaseUrl || !supabasePublishableKey) {
    throw new Error(
      "Set VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY (see .env.example)",
    );
  }
  return createClient(supabaseUrl, supabasePublishableKey, {
    auth: {
      storage: createRoutingStorage(remember),
      persistSession: true,
      detectSessionInUrl: true,
    },
  }) as SupabaseClient;
}

export function resetSupabaseClient(remember?: boolean): SupabaseClient {
  if (testClientInjected && client !== null) {
    return client;
  }
  const resolvedRemember = remember ?? readRememberPreference();
  if (client !== null && clientRemember === resolvedRemember) {
    return client;
  }
  const hadClient = client !== null;
  client = buildClient(resolvedRemember);
  clientRemember = resolvedRemember;
  if (hadClient) {
    notifyClientVersionChange();
  }
  return client;
}

export function getSupabaseClient(): SupabaseClient {
  if (client !== null) {
    return client;
  }
  const remember = readRememberPreference();
  client = buildClient(remember);
  clientRemember = remember;
  return client;
}

/** Test hook — replace the singleton client. */
export function setSupabaseClientForTests(mock: SupabaseClient | null): void {
  client = mock;
  clientRemember = null;
  testClientInjected = mock !== null;
}

export type OperatorRole = "admin" | "viewer";

export function roleFromAppMetadata(
  appMetadata: Record<string, unknown> | undefined,
): OperatorRole | null {
  const role = appMetadata?.["role"];
  if (role === "admin" || role === "viewer") {
    return role;
  }
  return null;
}
