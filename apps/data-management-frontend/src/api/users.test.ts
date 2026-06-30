import { afterEach, describe, expect, it, vi } from "vitest";

import {
  changeUserRole,
  deleteUser,
  disableUser,
  enableUser,
  forceSignout,
  inviteUser,
  listUsers,
  MechanismUnavailableError,
  resendInvite,
  resetUserPassword,
} from "./users";

const CLIENT = {
  baseUrl: "http://localhost:8001",
  modalKey: "proxy-key",
};
const JWT_CLIENT = {
  baseUrl: "http://localhost:8001",
  modalKey: "proxy-key",
  accessToken: "jwt-token",
};

const USER_ID = "11111111-1111-1111-1111-111111111111";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function lastInit(): RequestInit | undefined {
  const calls = vi.mocked(fetch).mock.calls;
  return calls[calls.length - 1]?.[1];
}

function lastUrl(): string {
  const calls = vi.mocked(fetch).mock.calls;
  return (calls[calls.length - 1]?.[0] as string | undefined) ?? "";
}

function bodyOf(init: RequestInit | undefined): unknown {
  return JSON.parse((init?.body as string | undefined) ?? "null");
}

function headersOf(init: RequestInit | undefined): Record<string, string> {
  return (init?.headers as Record<string, string> | undefined) ?? {};
}

const SUMMARY = {
  id: USER_ID,
  email: "admin@example.org",
  role: "admin",
  status: "active",
  created_at: "2026-06-01T00:00:00Z",
  last_sign_in_at: null,
};

describe("users API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("listUsers builds pagination params and sends the proxy header", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ users: [SUMMARY], total: 1, page: 2, page_size: 25 }),
      ),
    );
    const result = await listUsers(CLIENT, 2, 25);
    expect(result.users).toHaveLength(1);
    expect(lastUrl()).toContain("page=2");
    expect(lastUrl()).toContain("page_size=25");
    expect(headersOf(lastInit())["X-Vecinita-Proxy-Key"]).toBe("proxy-key");
  });

  it("listUsers uses default pagination when omitted", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ users: [], total: 0, page: 1, page_size: 50 }),
      ),
    );
    await listUsers(CLIENT);
    expect(lastUrl()).toContain("page=1");
    expect(lastUrl()).toContain("page_size=50");
  });

  it("listUsers throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("nope", { status: 500 })),
    );
    await expect(listUsers(CLIENT)).rejects.toThrow(/nope/);
  });

  it("listUsers uses the status fallback when the body is empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 503 })),
    );
    await expect(listUsers(CLIENT)).rejects.toThrow(/503/);
  });

  it("inviteUser posts email and role and sends the bearer token", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(SUMMARY, 201)),
    );
    await inviteUser(JWT_CLIENT, "new@example.org", "viewer");
    const init = lastInit();
    expect(init?.method).toBe("POST");
    expect(headersOf(init)["Authorization"]).toBe("Bearer jwt-token");
    expect(bodyOf(init)).toEqual({
      email: "new@example.org",
      role: "viewer",
    });
  });

  it("inviteUser throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("bad", { status: 422 })),
    );
    await expect(
      inviteUser(CLIENT, "x@example.org", "admin"),
    ).rejects.toThrow(/bad/);
  });

  it("changeUserRole patches the role", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(SUMMARY)));
    await changeUserRole(CLIENT, USER_ID, "viewer");
    const init = lastInit();
    expect(init?.method).toBe("PATCH");
    expect(lastUrl()).toBe(`${CLIENT.baseUrl}/admin/users/${USER_ID}/role`);
    expect(bodyOf(init)).toEqual({ role: "viewer" });
  });

  it("changeUserRole throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("err", { status: 400 })),
    );
    await expect(
      changeUserRole(CLIENT, USER_ID, "admin"),
    ).rejects.toThrow(/err/);
  });

  it("resendInvite posts to the resend endpoint", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
    await resendInvite(CLIENT, USER_ID);
    expect(lastUrl()).toBe(
      `${CLIENT.baseUrl}/admin/users/${USER_ID}/resend-invite`,
    );
    expect(lastInit()?.method).toBe("POST");
  });

  it("resendInvite throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("fail", { status: 409 })),
    );
    await expect(resendInvite(CLIENT, USER_ID)).rejects.toThrow(/fail/);
  });

  it("disableUser and enableUser hit their endpoints", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(jsonResponse(SUMMARY))
        .mockResolvedValueOnce(jsonResponse(SUMMARY)),
    );
    await disableUser(CLIENT, USER_ID);
    expect(lastUrl()).toBe(`${CLIENT.baseUrl}/admin/users/${USER_ID}/disable`);
    await enableUser(CLIENT, USER_ID);
    expect(lastUrl()).toBe(`${CLIENT.baseUrl}/admin/users/${USER_ID}/enable`);
  });

  it("disableUser throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("d", { status: 500 })),
    );
    await expect(disableUser(CLIENT, USER_ID)).rejects.toThrow(/d/);
  });

  it("enableUser throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("e", { status: 500 })),
    );
    await expect(enableUser(CLIENT, USER_ID)).rejects.toThrow(/e/);
  });

  it("deleteUser issues a DELETE", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
    await deleteUser(CLIENT, USER_ID);
    expect(lastUrl()).toBe(`${CLIENT.baseUrl}/admin/users/${USER_ID}`);
    expect(lastInit()?.method).toBe("DELETE");
  });

  it("deleteUser throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("del", { status: 404 })),
    );
    await expect(deleteUser(CLIENT, USER_ID)).rejects.toThrow(/del/);
  });

  it("resetUserPassword posts to the reset endpoint", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 202 })),
    );
    await resetUserPassword(CLIENT, USER_ID);
    expect(lastUrl()).toBe(
      `${CLIENT.baseUrl}/admin/users/${USER_ID}/reset-password`,
    );
  });

  it("resetUserPassword throws on HTTP error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("rp", { status: 500 })),
    );
    await expect(resetUserPassword(CLIENT, USER_ID)).rejects.toThrow(/rp/);
  });

  it("forceSignout posts to the signout endpoint on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse({ acknowledged: true }, 202)),
    );
    await forceSignout(CLIENT, USER_ID);
    expect(lastUrl()).toBe(`${CLIENT.baseUrl}/admin/users/${USER_ID}/signout`);
    expect(lastInit()?.method).toBe("POST");
  });

  it("forceSignout throws MechanismUnavailableError on 503 mechanism_unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          { detail: { code: "mechanism_unavailable", message: "no rpc" } },
          503,
        ),
      ),
    );
    await expect(forceSignout(CLIENT, USER_ID)).rejects.toBeInstanceOf(
      MechanismUnavailableError,
    );
  });

  it("forceSignout maps a non-JSON 503 body containing the code to the fallback", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("mechanism_unavailable", { status: 503 }),
      ),
    );
    await expect(forceSignout(CLIENT, USER_ID)).rejects.toBeInstanceOf(
      MechanismUnavailableError,
    );
  });

  it("forceSignout throws a generic error for a 503 without the code", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse({ detail: { code: "other" } }, 503),
      ),
    );
    const err = await forceSignout(CLIENT, USER_ID).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(Error);
    expect(err).not.toBeInstanceOf(MechanismUnavailableError);
  });

  it("forceSignout throws a generic error for other HTTP failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("forbidden", { status: 403 })),
    );
    await expect(forceSignout(CLIENT, USER_ID)).rejects.toThrow(/forbidden/);
  });

  it("forceSignout uses the status fallback for an empty non-503 body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("", { status: 500 })),
    );
    await expect(forceSignout(CLIENT, USER_ID)).rejects.toThrow(/500/);
  });
});
