export const PREWARM_POLICY_STORAGE_KEY = "vecinita.chat.prewarm-policy.v1";

const PREWARM_POLICIES = [
  "mount",
  "dwell",
  "focus",
  "first-keystroke",
] as const;

export type PrewarmTriggerPolicy = (typeof PREWARM_POLICIES)[number];

type StoredPolicyCounters = {
  prewarm_requested: number;
  ask_started: number;
};

type StoredPrewarmPolicyEnvelope = {
  version: 1;
  prewarm_requested: number;
  ask_started: number;
  pending_policy: PrewarmTriggerPolicy | null;
  policies: Record<PrewarmTriggerPolicy, StoredPolicyCounters>;
};

type PolicyEvidence = {
  prewarm_requested: number;
  ask_started: number;
  prewarm_to_ask_hit_rate: number;
};

export type PrewarmPolicyEvidence = {
  version: 1;
  prewarm_requested: number;
  ask_started: number;
  prewarm_to_ask_hit_rate: number;
  policies: Record<PrewarmTriggerPolicy, PolicyEvidence>;
};

function createEmptyEnvelope(): StoredPrewarmPolicyEnvelope {
  return {
    version: 1,
    prewarm_requested: 0,
    ask_started: 0,
    pending_policy: null,
    policies: {
      mount: { prewarm_requested: 0, ask_started: 0 },
      dwell: { prewarm_requested: 0, ask_started: 0 },
      focus: { prewarm_requested: 0, ask_started: 0 },
      "first-keystroke": { prewarm_requested: 0, ask_started: 0 },
    },
  };
}

function isStoredPolicyCounters(value: unknown): value is StoredPolicyCounters {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate["prewarm_requested"] === "number" &&
    typeof candidate["ask_started"] === "number"
  );
}

function isPrewarmTriggerPolicy(value: unknown): value is PrewarmTriggerPolicy {
  return (
    typeof value === "string" &&
    PREWARM_POLICIES.includes(value as PrewarmTriggerPolicy)
  );
}

function readEnvelope(): StoredPrewarmPolicyEnvelope {
  try {
    const raw = sessionStorage.getItem(PREWARM_POLICY_STORAGE_KEY);
    if (!raw) {
      return createEmptyEnvelope();
    }
    const parsed: unknown = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") {
      return createEmptyEnvelope();
    }
    const candidate = parsed as Record<string, unknown>;
    if (
      candidate["version"] !== 1 ||
      typeof candidate["prewarm_requested"] !== "number" ||
      typeof candidate["ask_started"] !== "number" ||
      !candidate["policies"] ||
      typeof candidate["policies"] !== "object"
    ) {
      return createEmptyEnvelope();
    }
    const policies = candidate["policies"] as Record<string, unknown>;
    const mount = policies["mount"];
    const dwell = policies["dwell"];
    const focus = policies["focus"];
    const firstKeystroke = policies["first-keystroke"];
    if (
      !isStoredPolicyCounters(mount) ||
      !isStoredPolicyCounters(dwell) ||
      !isStoredPolicyCounters(focus) ||
      !isStoredPolicyCounters(firstKeystroke)
    ) {
      return createEmptyEnvelope();
    }
    const pendingPolicy = isPrewarmTriggerPolicy(candidate["pending_policy"])
      ? candidate["pending_policy"]
      : null;
    return {
      version: 1,
      prewarm_requested: candidate["prewarm_requested"],
      ask_started: candidate["ask_started"],
      pending_policy: pendingPolicy,
      policies: {
        mount,
        dwell,
        focus,
        "first-keystroke": firstKeystroke,
      },
    };
  } catch {
    return createEmptyEnvelope();
  }
}

function writeEnvelope(envelope: StoredPrewarmPolicyEnvelope): void {
  try {
    sessionStorage.setItem(
      PREWARM_POLICY_STORAGE_KEY,
      JSON.stringify(envelope),
    );
  } catch {
    // Storage may be unavailable; evidence stays best-effort and in-memory only.
  }
}

function rate(askStarted: number, prewarmRequested: number): number {
  if (prewarmRequested <= 0) {
    return 0;
  }
  return askStarted / prewarmRequested;
}

export function recordPrewarmRequested(policy: PrewarmTriggerPolicy): void {
  const envelope = readEnvelope();
  envelope.prewarm_requested += 1;
  envelope.pending_policy = policy;
  envelope.policies[policy].prewarm_requested += 1;
  writeEnvelope(envelope);
}

export function recordAskStarted(): void {
  const envelope = readEnvelope();
  envelope.ask_started += 1;
  if (envelope.pending_policy) {
    envelope.policies[envelope.pending_policy].ask_started += 1;
    envelope.pending_policy = null;
  }
  writeEnvelope(envelope);
}

export function readPrewarmPolicyEvidence(): PrewarmPolicyEvidence {
  const envelope = readEnvelope();
  return {
    version: 1,
    prewarm_requested: envelope.prewarm_requested,
    ask_started: envelope.ask_started,
    prewarm_to_ask_hit_rate: rate(
      envelope.ask_started <= envelope.prewarm_requested
        ? envelope.ask_started
        : envelope.prewarm_requested,
      envelope.prewarm_requested,
    ),
    policies: {
      mount: {
        prewarm_requested: envelope.policies["mount"].prewarm_requested,
        ask_started: envelope.policies["mount"].ask_started,
        prewarm_to_ask_hit_rate: rate(
          envelope.policies["mount"].ask_started,
          envelope.policies["mount"].prewarm_requested,
        ),
      },
      dwell: {
        prewarm_requested: envelope.policies["dwell"].prewarm_requested,
        ask_started: envelope.policies["dwell"].ask_started,
        prewarm_to_ask_hit_rate: rate(
          envelope.policies["dwell"].ask_started,
          envelope.policies["dwell"].prewarm_requested,
        ),
      },
      focus: {
        prewarm_requested: envelope.policies["focus"].prewarm_requested,
        ask_started: envelope.policies["focus"].ask_started,
        prewarm_to_ask_hit_rate: rate(
          envelope.policies["focus"].ask_started,
          envelope.policies["focus"].prewarm_requested,
        ),
      },
      "first-keystroke": {
        prewarm_requested:
          envelope.policies["first-keystroke"].prewarm_requested,
        ask_started: envelope.policies["first-keystroke"].ask_started,
        prewarm_to_ask_hit_rate: rate(
          envelope.policies["first-keystroke"].ask_started,
          envelope.policies["first-keystroke"].prewarm_requested,
        ),
      },
    },
  };
}
