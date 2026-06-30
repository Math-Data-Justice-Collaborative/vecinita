import { useCallback } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/authContext";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useIdleTimeout } from "@/hooks/useIdleTimeout";
import { useAdminT } from "@/hooks/useAdminT";

export function IdleTimeoutGuard() {
  const tr = useAdminT();
  const navigate = useNavigate();
  const { session, signOut } = useAuth();

  const handleTimeout = useCallback(async () => {
    await signOut();
    await navigate("/login", {
      replace: true,
      state: { reason: "idle" },
    });
  }, [navigate, signOut]);

  const { showWarning, secondsRemaining, staySignedIn, signOutNow } =
    useIdleTimeout(Boolean(session), handleTimeout);

  return (
    <Dialog open={showWarning} onOpenChange={() => undefined}>
      <DialogContent data-testid="idle-timeout-warning">
        <DialogHeader>
          <DialogTitle>{tr("admin.auth.idleWarningTitle")}</DialogTitle>
          <DialogDescription>
            {tr("admin.auth.idleWarningBody", { seconds: secondsRemaining })}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            data-testid="idle-timeout-sign-out-now"
            onClick={() => {
              signOutNow();
            }}
          >
            {tr("admin.auth.idleSignOutNow")}
          </Button>
          <Button
            type="button"
            data-testid="idle-timeout-stay-signed-in"
            onClick={staySignedIn}
          >
            {tr("admin.auth.idleStaySignedIn")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
