import { describe, expect, it } from "vitest";
import {
  emailDraftStorageKey,
  parseGeneratedEmail,
  readEmailDraft,
  serializeEmailDrafts,
  type EmailDraft,
} from "./email-drafts";

function makeDraft(
  sourceId: string,
  body: string,
  subject = "A subject",
): EmailDraft {
  return {
    sourceId,
    to: "reader@example.com",
    cc: "",
    bcc: "",
    subject,
    body,
    updatedAt: 1,
  };
}

describe("email draft helpers", () => {
  it("separates a generated subject line from the email body", () => {
    expect(
      parseGeneratedEmail("Subject: Project update\n\nHello there,\nThanks."),
    ).toEqual({ subject: "Project update", body: "Hello there,\nThanks." });
  });

  it("preserves generated text as the body when there is no subject line", () => {
    expect(parseGeneratedEmail("Hello there,\nThanks.")).toEqual({
      subject: "",
      body: "Hello there,\nThanks.",
    });
  });

  it("scopes stored drafts to the signed-in user", () => {
    expect(emailDraftStorageKey("user-1")).not.toBe(
      emailDraftStorageKey("user-2"),
    );
    expect(emailDraftStorageKey(null)).toBe("pt-email-drafts:guest");
  });

  it("keeps independent generated response drafts separate", () => {
    const first = makeDraft("response-1", "Edited first response");
    const second = makeDraft("response-2", "Edited second response");
    const saved = serializeEmailDrafts(
      serializeEmailDrafts(null, first),
      second,
    );

    expect(readEmailDraft(saved, "response-1")?.body).toBe(
      "Edited first response",
    );
    expect(readEmailDraft(saved, "response-2")?.body).toBe(
      "Edited second response",
    );
  });

  it("updates an existing local draft without changing its source response", () => {
    const original = makeDraft("response-1", "Saved version");
    const edited = makeDraft("response-1", "New local version");
    const saved = serializeEmailDrafts(
      serializeEmailDrafts(null, original),
      edited,
    );

    expect(JSON.parse(saved)).toHaveLength(1);
    expect(readEmailDraft(saved, "response-1")?.body).toBe(
      "New local version",
    );
  });

  it("rejects malformed draft storage rather than silently replacing it", () => {
    expect(() => readEmailDraft("{", "response-1")).toThrow();
    expect(() => serializeEmailDrafts("{}", makeDraft("response-1", "Body")))
      .toThrow("Saved email drafts are not in a readable format.");
  });
});
