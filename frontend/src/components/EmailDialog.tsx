import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2, Loader2, Mail, Paperclip, X } from "lucide-react";
import { getBriefEmailPreview, sendBriefEmail } from "../api/client";
import type { EmailSendResult, Persona } from "../api/types";
import { PERSONA_LABELS } from "../lib/persona";

interface Props {
  open: boolean;
  onClose: () => void;
  meetingId: number;
  persona: Persona;
}

/**
 * "Send as email" — reviews the composed persona digest (Format C) before
 * sending. Real delivery only when SMTP is configured on the backend; otherwise
 * it's a "demo send" (composed + previewed, not delivered).
 */
export function EmailDialog({ open, onClose, meetingId, persona }: Props) {
  const [recipient, setRecipient] = useState("");
  const [result, setResult] = useState<EmailSendResult | null>(null);

  const { data: preview, isLoading } = useQuery({
    queryKey: ["email-preview", meetingId, persona],
    queryFn: () => getBriefEmailPreview(meetingId, persona),
    enabled: open,
  });

  // Reset per open + prefill the recipient once the preview arrives.
  useEffect(() => {
    if (open) setResult(null);
  }, [open, persona]);
  useEffect(() => {
    if (preview) setRecipient((r) => r || preview.recipient_default);
  }, [preview]);

  const mutation = useMutation({
    mutationFn: () => sendBriefEmail(meetingId, recipient.trim(), persona),
    onSuccess: (res) => setResult(res),
  });

  if (!open) return null;

  const canSend = recipient.trim().length > 3 && !mutation.isPending;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Send brief as email"
    >
      <div className="absolute inset-0 bg-ink-900/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 flex max-h-[88vh] w-full max-w-xl flex-col overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-700">
              <Mail className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-ink-900">Send as email</h2>
              <p className="text-xs text-ink-500">
                {PERSONA_LABELS[persona]} brief · review before sending
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-600"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Success / result state */}
        {result ? (
          <div className="flex flex-col items-center gap-3 px-6 py-12 text-center">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-2xl ${
                result.mode === "error"
                  ? "bg-[#fdeaec] text-bad"
                  : "bg-[#e7f6ee] text-good"
              }`}
            >
              {result.mode === "error" ? (
                <X className="h-6 w-6" />
              ) : (
                <CheckCircle2 className="h-6 w-6" />
              )}
            </div>
            <div>
              <h3 className="text-base font-semibold text-ink-900">
                {result.mode === "error"
                  ? "Could not send"
                  : result.mode === "demo"
                    ? "Demo send complete"
                    : "Email sent"}
              </h3>
              <p className="mt-1 max-w-sm text-sm text-muted">{result.message}</p>
            </div>
            <button type="button" className="btn-primary mt-2" onClick={onClose}>
              Done
            </button>
          </div>
        ) : (
          <>
            {/* Body */}
            <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-6 py-5">
              <div>
                <label className="label" htmlFor="email-to">
                  To
                </label>
                <input
                  id="email-to"
                  type="email"
                  className="input"
                  placeholder="name@company.com"
                  value={recipient}
                  onChange={(e) => setRecipient(e.target.value)}
                />
              </div>

              {isLoading && (
                <div className="flex items-center gap-2 py-8 text-sm text-muted">
                  <Loader2 className="h-4 w-4 animate-spin" /> Composing email…
                </div>
              )}

              {preview && (
                <>
                  <div>
                    <div className="label">Subject</div>
                    <div className="rounded-lg border border-line bg-ink-50 px-3 py-2 text-sm text-ink-800">
                      {preview.subject}
                    </div>
                  </div>

                  <div>
                    <div className="label">Preview</div>
                    <iframe
                      title="Email preview"
                      srcDoc={preview.body_html}
                      className="h-72 w-full rounded-lg border border-line bg-white"
                    />
                  </div>

                  <div className="flex items-center gap-2 rounded-lg border border-line bg-ink-50 px-3 py-2 text-sm text-ink-700">
                    <Paperclip className="h-4 w-4 text-ink-400" />
                    <span className="font-medium">{preview.attachment_filename}</span>
                    <span className="text-faint">— full brief attached</span>
                  </div>

                  {!preview.email_configured && (
                    <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
                      Demo mode — the email is composed and previewed but not actually
                      delivered. Add SMTP credentials to <code>backend/.env</code> to
                      send for real.
                    </p>
                  )}
                </>
              )}

              {mutation.isError && (
                <p className="rounded-lg bg-[#fdeaec] px-3 py-2 text-sm font-medium text-bad">
                  Could not reach the backend. Is it running?
                </p>
              )}
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-2 border-t border-line px-6 py-4">
              <button type="button" className="btn-secondary" onClick={onClose}>
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={!canSend}
                onClick={() => mutation.mutate()}
              >
                {mutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Mail className="h-4 w-4" />
                )}
                {preview?.email_configured ? "Send email" : "Confirm send"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
