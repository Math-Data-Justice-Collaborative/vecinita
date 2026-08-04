/**
 * F69 / UJ-074 — prefer Supabase email; else truncated actor_id (S026-D19).
 */

const UUID_PREFIX_LEN = 8;

export function formatActorLabel(
  actorEmail: string | null | undefined,
  actorId: string | null | undefined,
): string {
  const email = actorEmail?.trim();
  if (email) return email;
  const id = actorId?.trim();
  if (!id) return "—";
  if (id.length <= UUID_PREFIX_LEN) return id;
  return `${id.slice(0, UUID_PREFIX_LEN)}…`;
}
