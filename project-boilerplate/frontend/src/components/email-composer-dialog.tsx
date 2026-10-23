"use client";

import {
  forwardRef,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import { AlertCircle, Check, Copy, Mail, Save, Send, X } from "lucide-react";
import {
  emailDraftStorageKey,
  parseGeneratedEmail,
  readEmailDraft,
  serializeEmailDrafts,
  type EmailDraft,
} from "@/lib/email-drafts";

interface EmailComposerDialogProps {
  sourceId: string;
  personaLabel: string;
  generatedText: string;
}

export interface EmailComposerDialogHandle {
  open: () => void;
}

function storageKey(): string {
  return emailDraftStorageKey(localStorage.getItem("pt-user-id"));
}

export const EmailComposerDialog = forwardRef<
  EmailComposerDialogHandle,
  EmailComposerDialogProps
>(function EmailComposerDialog(
  { sourceId, personaLabel, generatedText },
  forwardedRef,
) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [to, setTo] = useState("");
  const [cc, setCc] = useState("");
  const [bcc, setBcc] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState(generatedText);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  useImperativeHandle(forwardedRef, () => ({
    open() {
      const dialog = dialogRef.current;
      if (!dialog || dialog.open) return;

      const generated = parseGeneratedEmail(generatedText);
      try {
        const saved = readEmailDraft(
          localStorage.getItem(storageKey()),
          sourceId,
        );
        setTo(saved?.to ?? "");
        setCc(saved?.cc ?? "");
        setBcc(saved?.bcc ?? "");
        setSubject(saved?.subject ?? generated.subject);
        setBody(saved?.body ?? generated.body);
        setNotice("");
        setError("");
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Could not load the saved local draft.",
        );
        setTo("");
        setCc("");
        setBcc("");
        setSubject(generated.subject);
        setBody(generated.body);
      }
      dialog.showModal();
    },
  }), [generatedText, sourceId]);

  const closeDialog = () => {
    const dialog = dialogRef.current;
    if (dialog?.open) dialog.close();
  };

  const saveDraft = () => {
    setError("");
    setNotice("");
    try {
      const draft: EmailDraft = {
        sourceId,
        to: to.trim(),
        cc: cc.trim(),
        bcc: bcc.trim(),
        subject: subject.trim(),
        body,
        updatedAt: Date.now(),
      };
      localStorage.setItem(
        storageKey(),
        serializeEmailDrafts(localStorage.getItem(storageKey()), draft),
      );
      setNotice("Draft saved on this device. It has not been saved to Gmail.");
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "Could not save this draft on your device.",
      );
    }
  };

  const copyEmail = async () => {
    setError("");
    setNotice("");
    try {
      await navigator.clipboard.writeText(body);
      setNotice("Email copied.");
    } catch {
      setError("Could not access the clipboard. Check your browser permissions.");
    }
  };

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={`email-composer-title-${sourceId}`}
      className="m-auto max-h-[90dvh] w-[min(680px,calc(100vw-24px))] overflow-y-auto rounded-2xl border border-white/10 bg-[#111111] p-0 text-white shadow-2xl backdrop:bg-black/70"
    >
      <form onSubmit={(event) => event.preventDefault()} className="flex flex-col">
        <div className="flex items-start justify-between border-b border-white/[0.08] px-5 py-4">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.08]">
              <Mail className="h-4 w-4 text-white/70" aria-hidden="true" />
            </div>
            <div>
              <h2
                id={`email-composer-title-${sourceId}`}
                className="text-base font-semibold"
              >
                Review email
              </h2>
              <p className="mt-1 text-xs text-white/45">
                Draft for {personaLabel}. Your generated response stays unchanged.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={closeDialog}
            aria-label="Close email composer"
            title="Close"
            className="rounded-lg p-2 text-white/45 transition hover:bg-white/[0.08] hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <div className="space-y-4 px-5 py-5">
          <label className="block text-xs font-medium text-white/65">
            To
            <input
              type="text"
              autoComplete="email"
              value={to}
              onChange={(event) => setTo(event.target.value)}
              placeholder="name@example.com"
              className="mt-1.5 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-sm text-white placeholder:text-white/25 focus:border-white/30 focus:outline-none focus:ring-2 focus:ring-white/10"
            />
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-white/65">
              CC <span className="font-normal text-white/35">Optional</span>
              <input
                type="text"
                value={cc}
                onChange={(event) => setCc(event.target.value)}
                placeholder="Separate multiple addresses with commas"
                className="mt-1.5 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-sm text-white placeholder:text-white/25 focus:border-white/30 focus:outline-none focus:ring-2 focus:ring-white/10"
              />
            </label>
            <label className="block text-xs font-medium text-white/65">
              BCC <span className="font-normal text-white/35">Optional</span>
              <input
                type="text"
                value={bcc}
                onChange={(event) => setBcc(event.target.value)}
                placeholder="Separate multiple addresses with commas"
                className="mt-1.5 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-sm text-white placeholder:text-white/25 focus:border-white/30 focus:outline-none focus:ring-2 focus:ring-white/10"
              />
            </label>
          </div>

          <label className="block text-xs font-medium text-white/65">
            Subject
            <input
              type="text"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              placeholder="Add a subject"
              className="mt-1.5 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-sm text-white placeholder:text-white/25 focus:border-white/30 focus:outline-none focus:ring-2 focus:ring-white/10"
            />
          </label>

          <label className="block text-xs font-medium text-white/65">
            Email body
            <textarea
              value={body}
              onChange={(event) => setBody(event.target.value)}
              rows={9}
              className="mt-1.5 w-full resize-y rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-sm leading-6 text-white placeholder:text-white/25 focus:border-white/30 focus:outline-none focus:ring-2 focus:ring-white/10"
            />
          </label>

          <div
            role="status"
            aria-live="polite"
            className="rounded-xl border border-amber-300/15 bg-amber-300/[0.06] px-3.5 py-3 text-xs leading-5 text-amber-100/75"
          >
            Gmail is not connected. Sending and Gmail draft saving are unavailable.
            You can save a clearly labeled local draft on this device.
          </div>

          {notice && (
            <p
              role="status"
              aria-live="polite"
              className="flex items-center gap-2 text-xs text-emerald-300"
            >
              <Check className="h-4 w-4 shrink-0" aria-hidden="true" />
              {notice}
            </p>
          )}
          {error && (
            <p role="alert" className="flex items-center gap-2 text-xs text-red-300">
              <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
              {error}
            </p>
          )}
        </div>

        <div className="flex flex-col-reverse gap-2 border-t border-white/[0.08] px-5 py-4 sm:flex-row sm:items-center">
          <button
            type="button"
            onClick={closeDialog}
            className="rounded-lg px-3.5 py-2 text-sm text-white/65 transition hover:bg-white/[0.06] hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
          >
            Cancel
          </button>
          <div className="flex flex-wrap gap-2 sm:ml-auto">
            <button
              type="button"
              onClick={() => void copyEmail()}
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 px-3.5 py-2 text-sm text-white/75 transition hover:bg-white/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
            >
              <Copy className="h-4 w-4" aria-hidden="true" />
              Copy
            </button>
            <button
              type="button"
              onClick={saveDraft}
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 px-3.5 py-2 text-sm text-white/75 transition hover:bg-white/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
            >
              <Save className="h-4 w-4" aria-hidden="true" />
              Save locally
            </button>
            <button
              type="button"
              disabled
              title="Configure a supported Gmail MCP server to send email"
              className="inline-flex cursor-not-allowed items-center justify-center gap-2 rounded-lg bg-white px-3.5 py-2 text-sm font-semibold text-black opacity-40"
            >
              <Send className="h-4 w-4" aria-hidden="true" />
              Send email
            </button>
          </div>
        </div>
      </form>
    </dialog>
  );
});