import type { UserListResponse, UserRole, UserSummary } from "./types";

export interface UsersClientOptions {
  baseUrl: string;
  modalKey: string;
  accessToken?: string | undefined;
}

function usersHeaders(options: UsersClientOptions): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Vecinita-Proxy-Key": options.modalKey,
  };
  if (options.accessToken) {
    headers["Authorization"] = `Bearer ${options.accessToken}`;
  }
  return headers;
}

async function parseError(response: Response, label: string): Promise<never> {
  const detail = await response.text();
  throw new Error(detail || `${label} failed (${String(response.status)})`);
}

/**
 * Raised when the `admin_delete_user_sessions` RPC is not applied to the Supabase
 * project, so force sign-out is unavailable (backend `503 mechanism_unavailable`).
 * Callers should advise the admin to use Disable (ban) as the guaranteed lockout (UJ-036).
 */
export class MechanismUnavailableError extends Error {
  constructor(message = "Session-revoke mechanism is unavailable") {
    super(message);
    this.name = "MechanismUnavailableError";
  }
}

/**
 * Raised when Resend test-send secrets are unset on the backend (`503 email_unconfigured`).
 */
export class EmailUnconfiguredError extends Error {
  constructor(message = "Email deliverability test-send is not configured") {
    super(message);
    this.name = "EmailUnconfiguredError";
  }
}

function isMechanismUnavailable(status: number, body: string): boolean {
  if (status !== 503) return false;
  try {
    const parsed = JSON.parse(body) as { detail?: { code?: unknown } };
    return parsed.detail?.code === "mechanism_unavailable";
  } catch {
    return body.includes("mechanism_unavailable");
  }
}

function isEmailUnconfigured(status: number, body: string): boolean {
  if (status !== 503) return false;
  try {
    const parsed = JSON.parse(body) as { detail?: { code?: unknown } };
    return parsed.detail?.code === "email_unconfigured";
  } catch {
    return body.includes("email_unconfigured");
  }
}

export async function listUsers(
  options: UsersClientOptions,
  page = 1,
  pageSize = 50,
  q?: string,
): Promise<UserListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  const trimmed = q?.trim();
  if (trimmed) {
    params.set("q", trimmed);
  }
  const response = await fetch(`${options.baseUrl}/admin/users?${params}`, {
    headers: usersHeaders(options),
  });
  if (!response.ok) {
    return parseError(response, "List users");
  }
  return response.json() as Promise<UserListResponse>;
}

export async function inviteUser(
  options: UsersClientOptions,
  email: string,
  role: UserRole,
): Promise<UserSummary> {
  const response = await fetch(`${options.baseUrl}/admin/users/invite`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...usersHeaders(options),
    },
    body: JSON.stringify({ email, role }),
  });
  if (!response.ok) {
    return parseError(response, "Invite user");
  }
  return response.json() as Promise<UserSummary>;
}

export async function changeUserRole(
  options: UsersClientOptions,
  userId: string,
  role: UserRole,
): Promise<UserSummary> {
  const response = await fetch(
    `${options.baseUrl}/admin/users/${userId}/role`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...usersHeaders(options),
      },
      body: JSON.stringify({ role }),
    },
  );
  if (!response.ok) {
    return parseError(response, "Change role");
  }
  return response.json() as Promise<UserSummary>;
}

export async function resendInvite(
  options: UsersClientOptions,
  userId: string,
): Promise<void> {
  const response = await fetch(
    `${options.baseUrl}/admin/users/${userId}/resend-invite`,
    {
      method: "POST",
      headers: usersHeaders(options),
    },
  );
  if (!response.ok) {
    return parseError(response, "Resend invite");
  }
}

export async function disableUser(
  options: UsersClientOptions,
  userId: string,
): Promise<UserSummary> {
  const response = await fetch(
    `${options.baseUrl}/admin/users/${userId}/disable`,
    {
      method: "POST",
      headers: usersHeaders(options),
    },
  );
  if (!response.ok) {
    return parseError(response, "Disable user");
  }
  return response.json() as Promise<UserSummary>;
}

export async function enableUser(
  options: UsersClientOptions,
  userId: string,
): Promise<UserSummary> {
  const response = await fetch(
    `${options.baseUrl}/admin/users/${userId}/enable`,
    {
      method: "POST",
      headers: usersHeaders(options),
    },
  );
  if (!response.ok) {
    return parseError(response, "Enable user");
  }
  return response.json() as Promise<UserSummary>;
}

export async function deleteUser(
  options: UsersClientOptions,
  userId: string,
): Promise<void> {
  const response = await fetch(`${options.baseUrl}/admin/users/${userId}`, {
    method: "DELETE",
    headers: usersHeaders(options),
  });
  if (!response.ok) {
    return parseError(response, "Delete user");
  }
}

export async function resetUserPassword(
  options: UsersClientOptions,
  userId: string,
): Promise<void> {
  const response = await fetch(
    `${options.baseUrl}/admin/users/${userId}/reset-password`,
    {
      method: "POST",
      headers: usersHeaders(options),
    },
  );
  if (!response.ok) {
    return parseError(response, "Reset password");
  }
}

export async function forceSignout(
  options: UsersClientOptions,
  userId: string,
): Promise<void> {
  const response = await fetch(
    `${options.baseUrl}/admin/users/${userId}/signout`,
    {
      method: "POST",
      headers: usersHeaders(options),
    },
  );
  if (!response.ok) {
    const body = await response.text();
    if (isMechanismUnavailable(response.status, body)) {
      throw new MechanismUnavailableError();
    }
    throw new Error(
      body || `Force sign-out failed (${String(response.status)})`,
    );
  }
}

export interface EmailTestResult {
  message_id: string;
}

export async function sendTestEmail(
  options: UsersClientOptions,
  to: string,
): Promise<EmailTestResult> {
  const response = await fetch(`${options.baseUrl}/admin/email/test`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...usersHeaders(options),
    },
    body: JSON.stringify({ to: to.trim() }),
  });
  if (!response.ok) {
    const body = await response.text();
    if (isEmailUnconfigured(response.status, body)) {
      throw new EmailUnconfiguredError();
    }
    throw new Error(
      body || `Send test email failed (${String(response.status)})`,
    );
  }
  return response.json() as Promise<EmailTestResult>;
}
