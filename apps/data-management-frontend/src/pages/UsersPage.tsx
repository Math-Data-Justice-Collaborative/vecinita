import { useCallback, useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { type StringMessageKey } from "vecinita-frontend-i18n";
import { useLocale } from "vecinita-frontend-ui";

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
} from "@/api/users";
import type { UserRole, UserStatus, UserSummary } from "@/api/types";
import { useAuth, useIsAdmin } from "@/auth/authContext";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { requireAdminConfig } from "@/config";
import { useAdminT } from "@/hooks/useAdminT";
import { formatLocaleDateTime } from "@/lib/formatLocaleDateTime";

type BadgeVariant = "default" | "secondary" | "destructive" | "outline";

const STATUS_VARIANT: Record<UserStatus, BadgeVariant> = {
  active: "default",
  invited: "outline",
  disabled: "destructive",
};

const STATUS_KEY: Record<UserStatus, StringMessageKey> = {
  active: "admin.users.status.active",
  invited: "admin.users.status.invited",
  disabled: "admin.users.status.disabled",
};

const ROLE_KEY: Record<UserRole, StringMessageKey> = {
  admin: "admin.users.roleAdmin",
  viewer: "admin.users.roleViewer",
};

export function UsersPage() {
  const tr = useAdminT();
  const { locale } = useLocale();
  const { loading: authLoading } = useAuth();
  const isAdmin = useIsAdmin();
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<UserRole>("viewer");
  const [inviteBusy, setInviteBusy] = useState(false);
  const [actionBusy, setActionBusy] = useState<string | null>(null);
  const [signoutFallback, setSignoutFallback] = useState<string | null>(null);

  const load = useCallback(async (isActive: () => boolean = () => true) => {
    setLoading(true);
    setError(null);
    try {
      const client = requireAdminConfig();
      const result = await listUsers(client);
      if (!isActive()) return;
      setUsers(result.users);
    } catch (err) {
      if (!isActive()) return;
      setError(
        err instanceof Error ? err.message : tr("admin.users.loadFailed"),
      );
    } finally {
      if (isActive()) setLoading(false);
    }
  }, [tr]);

  useEffect(() => {
    let active = true;
    void load(() => active);
    return () => {
      active = false;
    };
  }, [load]);

  if (authLoading) {
    return (
      <p className="text-muted-foreground" data-testid="users-auth-loading">
        {tr("shared.loading")}
      </p>
    );
  }

  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleInvite() {
    setInviteBusy(true);
    setError(null);
    try {
      const client = requireAdminConfig();
      await inviteUser(client, inviteEmail.trim(), inviteRole);
      setInviteOpen(false);
      setInviteEmail("");
      setInviteRole("viewer");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("admin.users.loadFailed"));
    } finally {
      setInviteBusy(false);
    }
  }

  async function runAction(userId: string, action: () => Promise<void>) {
    setActionBusy(userId);
    setError(null);
    try {
      await action();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("admin.users.loadFailed"));
    } finally {
      setActionBusy(null);
    }
  }

  async function handleForceSignout(userId: string) {
    setActionBusy(userId);
    setError(null);
    setSignoutFallback(null);
    try {
      const client = requireAdminConfig();
      await forceSignout(client, userId);
      await load();
    } catch (err) {
      if (err instanceof MechanismUnavailableError) {
        setSignoutFallback(tr("admin.users.forceSignoutFallback"));
      } else {
        setError(
          err instanceof Error ? err.message : tr("admin.users.loadFailed"),
        );
      }
    } finally {
      setActionBusy(null);
    }
  }

  return (
    <div className="space-y-6" data-testid="users-page">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            {tr("admin.users.title")}
          </h2>
          <p className="text-muted-foreground">{tr("admin.users.subtitle")}</p>
        </div>
        <Button
          type="button"
          data-testid="users-invite-open"
          onClick={() => {
            setInviteOpen(true);
          }}
        >
          {tr("admin.users.invite")}
        </Button>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}

      {signoutFallback ? (
        <p
          role="alert"
          data-testid="force-signout-fallback"
          className="text-sm text-destructive"
        >
          {signoutFallback}
        </p>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>{tr("admin.users.title")}</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground">{tr("shared.loading")}</p>
          ) : users.length === 0 ? (
            <p className="text-muted-foreground">{tr("admin.users.empty")}</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{tr("admin.users.columnEmail")}</TableHead>
                  <TableHead>{tr("admin.users.columnRole")}</TableHead>
                  <TableHead>{tr("admin.users.columnStatus")}</TableHead>
                  <TableHead>{tr("admin.users.columnLastSignIn")}</TableHead>
                  <TableHead>{tr("admin.users.columnActions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id} data-testid="user-row">
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      {user.role ? tr(ROLE_KEY[user.role]) : "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={STATUS_VARIANT[user.status]}>
                        {tr(STATUS_KEY[user.status])}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {user.last_sign_in_at
                        ? formatLocaleDateTime(locale, user.last_sign_in_at)
                        : "—"}
                    </TableCell>
                    <TableCell className="space-x-1">
                      {user.status === "invited" ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={actionBusy === user.id}
                          data-testid={`resend-invite-${user.id}`}
                          onClick={() => {
                            void runAction(user.id, async () => {
                              const client = requireAdminConfig();
                              await resendInvite(client, user.id);
                            });
                          }}
                        >
                          {tr("admin.users.action.resendInvite")}
                        </Button>
                      ) : null}
                      {user.status === "disabled" ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={actionBusy === user.id}
                          data-testid={`enable-user-${user.id}`}
                          onClick={() => {
                            void runAction(user.id, async () => {
                              const client = requireAdminConfig();
                              await enableUser(client, user.id);
                            });
                          }}
                        >
                          {tr("admin.users.action.enable")}
                        </Button>
                      ) : (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={actionBusy === user.id}
                          data-testid={`disable-user-${user.id}`}
                          onClick={() => {
                            void runAction(user.id, async () => {
                              const client = requireAdminConfig();
                              await disableUser(client, user.id);
                            });
                          }}
                        >
                          {tr("admin.users.action.disable")}
                        </Button>
                      )}
                      {user.role === "viewer" ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={actionBusy === user.id}
                          data-testid={`promote-user-${user.id}`}
                          onClick={() => {
                            void runAction(user.id, async () => {
                              const client = requireAdminConfig();
                              await changeUserRole(client, user.id, "admin");
                            });
                          }}
                        >
                          {tr("admin.users.action.makeAdmin")}
                        </Button>
                      ) : (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={actionBusy === user.id}
                          data-testid={`demote-user-${user.id}`}
                          onClick={() => {
                            void runAction(user.id, async () => {
                              const client = requireAdminConfig();
                              await changeUserRole(client, user.id, "viewer");
                            });
                          }}
                        >
                          {tr("admin.users.action.makeViewer")}
                        </Button>
                      )}
                      {user.status === "active" ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={actionBusy === user.id}
                          data-testid={`force-signout-${user.id}`}
                          onClick={() => {
                            void handleForceSignout(user.id);
                          }}
                        >
                          {tr("admin.users.action.forceSignout")}
                        </Button>
                      ) : null}
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={actionBusy === user.id}
                        data-testid={`reset-password-${user.id}`}
                        onClick={() => {
                          void runAction(user.id, async () => {
                            const client = requireAdminConfig();
                            await resetUserPassword(client, user.id);
                          });
                        }}
                      >
                        {tr("admin.users.action.resetPassword")}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="destructive"
                        disabled={actionBusy === user.id}
                        data-testid={`delete-user-${user.id}`}
                        onClick={() => {
                          void runAction(user.id, async () => {
                            const client = requireAdminConfig();
                            await deleteUser(client, user.id);
                          });
                        }}
                      >
                        {tr("admin.users.action.delete")}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
        <DialogContent data-testid="users-invite-dialog">
          <DialogHeader>
            <DialogTitle>{tr("admin.users.inviteTitle")}</DialogTitle>
            <DialogDescription>
              {tr("admin.users.inviteSubtitle")}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="invite-email">{tr("admin.users.inviteEmail")}</Label>
              <Input
                id="invite-email"
                type="email"
                value={inviteEmail}
                data-testid="users-invite-email"
                onChange={(e) => {
                  setInviteEmail(e.target.value);
                }}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="invite-role">{tr("admin.users.inviteRole")}</Label>
              <Select
                value={inviteRole}
                onValueChange={(value: string) => {
                  setInviteRole(value as UserRole);
                }}
              >
                <SelectTrigger id="invite-role" data-testid="users-invite-role">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="viewer">
                    {tr("admin.users.roleViewer")}
                  </SelectItem>
                  <SelectItem value="admin">
                    {tr("admin.users.roleAdmin")}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              data-testid="users-invite-submit"
              disabled={inviteBusy || !inviteEmail.trim()}
              onClick={() => {
                void handleInvite();
              }}
            >
              {inviteBusy
                ? tr("admin.users.sendingInvite")
                : tr("admin.users.sendInvite")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
