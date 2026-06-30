import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { getSupabaseClient } from "@/auth/supabaseClient";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAdminT } from "@/hooks/useAdminT";

export function ForgotPasswordPage() {
  const tr = useAdminT();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const supabase = getSupabaseClient();
      const redirectTo = `${window.location.origin}/reset-password`;
      const { error: resetError } = await supabase.auth.resetPasswordForEmail(
        email.trim(),
        { redirectTo },
      );
      if (resetError) {
        throw resetError;
      }
      setSent(true);
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
        data-testid="forgot-password-form"
      >
        <h1 className="text-xl font-semibold">
          {tr("admin.auth.forgotPasswordTitle")}
        </h1>
        <p className="text-sm text-muted-foreground">
          {tr("admin.auth.forgotPasswordSubtitle")}
        </p>
        {sent ? (
          <p className="text-sm text-muted-foreground" role="status">
            {tr("admin.auth.resetLinkSent")}
          </p>
        ) : (
          <div className="space-y-2">
            <Label htmlFor="forgot-email">{tr("admin.auth.email")}</Label>
            <Input
              id="forgot-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
              }}
              required
            />
          </div>
        )}
        {error ? (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : null}
        {!sent ? (
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting
              ? tr("admin.auth.sendingResetLink")
              : tr("admin.auth.sendResetLink")}
          </Button>
        ) : null}
        <p className="text-center text-sm">
          <Link to="/login" className="text-primary underline-offset-4 hover:underline">
            {tr("admin.auth.backToLogin")}
          </Link>
        </p>
      </form>
    </div>
  );
}
