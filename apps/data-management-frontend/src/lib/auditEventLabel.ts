import type { StringMessageKey } from "vecinita-frontend-i18n";

const AUDIT_EVENT_LABELS: Partial<Record<string, StringMessageKey>> = {
  "user.invited": "admin.audit.event.user.invited",
  "user.role_changed": "admin.audit.event.user.role_changed",
  "user.disabled": "admin.audit.event.user.disabled",
  "user.enabled": "admin.audit.event.user.enabled",
  "user.deleted": "admin.audit.event.user.deleted",
  "user.reset_password": "admin.audit.event.user.reset_password",
  "user.signed_out": "admin.audit.event.user.signed_out",
  "email.test_sent": "admin.audit.event.email.test_sent",
};

export function auditEventLabelKey(
  eventType: string,
): StringMessageKey | undefined {
  return AUDIT_EVENT_LABELS[eventType];
}
