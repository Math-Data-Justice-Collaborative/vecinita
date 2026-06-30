import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";

import { useAuth } from "@/auth/authContext";
import { readRememberPreference } from "@/auth/supabaseClient";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAdminT } from "@/hooks/useAdminT";

export function LoginPage() {
  const tr = useAdminT();
  const { session, signIn } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(() => readRememberPreference());
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const from =
    (location.state as { from?: string } | null)?.from ?? "/dashboard";

  if (session) {
    return <Navigate to={from} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signIn(email.trim(), password, remember);
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
        data-testid="login-form"
      >
        <h1 className="text-xl font-semibold">{tr("admin.auth.loginTitle")}</h1>
        <p className="text-sm text-muted-foreground">
          {tr("admin.auth.loginSubtitle")}
        </p>
        <div className="space-y-2">
          <Label htmlFor="email">{tr("admin.auth.email")}</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
            }}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">{tr("admin.auth.password")}</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
            }}
            required
          />
        </div>
        <div className="flex items-center gap-2">
          <Checkbox
            id="remember-me"
            data-testid="remember-me"
            checked={remember}
            onCheckedChange={(checked) => {
              setRemember(checked === true);
            }}
          />
          <Label htmlFor="remember-me" className="text-sm font-normal">
            {tr("admin.auth.rememberMe")}
          </Label>
        </div>
        {error ? (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        ) : null}
        <Button type="submit" className="w-full" disabled={submitting}>
          {submitting ? tr("admin.auth.signingIn") : tr("admin.auth.signIn")}
        </Button>
        <p className="text-center text-sm">
          <Link
            to="/forgot-password"
            className="text-primary underline-offset-4 hover:underline"
          >
            {tr("admin.auth.forgotPassword")}
          </Link>
        </p>
      </form>
    </div>
  );
}
