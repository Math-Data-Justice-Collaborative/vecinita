import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { type StringMessageKey } from "vecinita-frontend-i18n";

import { getSupabaseClient } from "@/auth/supabaseClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAdminT } from "@/hooks/useAdminT";

type PasswordFlowVariant = "reset" | "invite";

const TITLE_KEY: Record<PasswordFlowVariant, StringMessageKey> = {
  reset: "admin.auth.setPasswordTitle",
  invite: "admin.auth.acceptInviteTitle",
};

const SUBTITLE_KEY: Record<PasswordFlowVariant, StringMessageKey> = {
  reset: "admin.auth.setPasswordSubtitle",
  invite: "admin.auth.acceptInviteSubtitle",
};

export function SetPasswordPage({ variant }: { variant: PasswordFlowVariant }) {
  const tr = useAdminT();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError(tr("admin.auth.passwordMismatch"));
      return;
    }
    setSubmitting(true);
    try {
      const supabase = getSupabaseClient();
      const { error: updateError } = await supabase.auth.updateUser({
        password,
      });
      if (updateError) {
        throw updateError;
      }
      setDone(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : tr("admin.auth.loginFailed"),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <form
        onSubmit={(e) => {
          void handleSubmit(e);
        }}
        className="w-full max-w-sm space-y-4 rounded-lg border bg-card p-6 shadow-sm"
        data-testid={`${variant}-password-form`}
      >
        <h1 className="text-xl font-semibold">{tr(TITLE_KEY[variant])}</h1>
        <p className="text-sm text-muted-foreground">
          {tr(SUBTITLE_KEY[variant])}
        </p>
        {done ? (
          <p className="text-sm text-muted-foreground" role="status">
            {tr("admin.auth.passwordUpdated")}
          </p>
        ) : (
          <>
            <div className="space-y-2">
              <Label htmlFor="new-password">{tr("admin.auth.password")}</Label>
              <Input
                id="new-password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                }}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">
                {tr("admin.auth.confirmPassword")}
              </Label>
              <Input
                id="confirm-password"
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => {
                  setConfirm(e.target.value);
                }}
                required
              />
            </div>
          </>
        )}
        {error ? (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : null}
        {!done ? (
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting
              ? tr("admin.auth.updatingPassword")
              : tr("admin.auth.updatePassword")}
          </Button>
        ) : null}
        <p className="text-center text-sm">
          <Link
            to="/login"
            className="text-primary underline-offset-4 hover:underline"
          >
            {tr("admin.auth.backToLogin")}
          </Link>
        </p>
      </form>
    </div>
  );
}
