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

export async function listUsers(
  options: UsersClientOptions,
  page = 1,
  pageSize = 50,
): Promise<UserListResponse> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
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
  const response = await fetch(`${options.baseUrl}/admin/users/${userId}/role`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...usersHeaders(options),
    },
    body: JSON.stringify({ role }),
  });
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
