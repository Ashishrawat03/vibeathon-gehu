export interface EmailDraft {
  sourceId: string;
  to: string;
  cc: string;
  bcc: string;
  subject: string;
  body: string;
  updatedAt: number;
}

function isEmailDraft(value: unknown): value is EmailDraft {
  if (typeof value !== "object" || value === null) return false;
  return (
    "sourceId" in value &&
    typeof value.sourceId === "string" &&
    "to" in value &&
    typeof value.to === "string" &&
    "cc" in value &&
    typeof value.cc === "string" &&
    "bcc" in value &&
    typeof value.bcc === "string" &&
    "subject" in value &&
    typeof value.subject === "string" &&
    "body" in value &&
    typeof value.body === "string" &&
    "updatedAt" in value &&
    typeof value.updatedAt === "number"
  );
}

export function emailDraftStorageKey(userId: string | null): string {
  return `pt-email-drafts:${userId || "guest"}`;
}

export function parseGeneratedEmail(text: string): {
  subject: string;
  body: string;
} {
  const match = text.match(/^\s*Subject:\s*(.+?)(?:\r?\n)+/i);
  if (!match) return { subject: "", body: text };
  return {
    subject: match[1].trim(),
    body: text.slice(match[0].length).trimStart(),
  };
}

export function readEmailDraft(raw: string | null, sourceId: string): EmailDraft | null {
  if (!raw) return null;

  const drafts: unknown = JSON.parse(raw);
  if (!Array.isArray(drafts)) {
    throw new Error("Saved email drafts are not in a readable format.");
  }

  return (
    drafts.find(
      (item): item is EmailDraft =>
        isEmailDraft(item) && item.sourceId === sourceId,
    ) ?? null
  );
}

export function serializeEmailDrafts(
  raw: string | null,
  draft: EmailDraft,
): string {
  const drafts: unknown = raw ? JSON.parse(raw) : [];
  if (!Array.isArray(drafts)) {
    throw new Error("Saved email drafts are not in a readable format.");
  }

  const next = drafts.filter(
    (item) => !isEmailDraft(item) || item.sourceId !== draft.sourceId,
  );
  return JSON.stringify([draft, ...next]);
}
