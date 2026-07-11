import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Radar, Send } from "lucide-react";
import { getChat, postChat } from "../api/client";
import type { ChatMessageRead } from "../api/types";
import { MarkdownView } from "./MarkdownView";

interface Props {
  meetingId: number;
  disabled?: boolean;
}

/** Scout — the grounded, per-account assistant. */
export function ChatPanel({ meetingId, disabled }: Props) {
  const queryClient = useQueryClient();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: messages = [] } = useQuery({
    queryKey: ["chat", meetingId],
    queryFn: () => getChat(meetingId),
    enabled: !disabled,
  });

  const mutation = useMutation({
    mutationFn: (question: string) => postChat(meetingId, question),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat", meetingId] });
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, mutation.isPending]);

  const send = () => {
    const q = input.trim();
    if (!q || mutation.isPending) return;
    setInput("");
    mutation.mutate(q);
  };

  // Detect a "not grounded" assistant answer to style it distinctly (amber).
  const notGrounded = (m: ChatMessageRead) =>
    m.role === "assistant" &&
    /not in the sources|no supporting sources|not supported/i.test(m.content);

  return (
    <div className="card flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2.5 border-b border-line px-4 py-3.5">
        <span
          aria-hidden
          className="grid h-[30px] w-[30px] place-items-center rounded-[9px] bg-gradient-to-br from-brand-600 to-[#6d70ff] text-base font-bold text-white"
        >
          ◎
        </span>
        <div className="leading-tight">
          <div className="text-[15px] font-bold text-ink-900">Scout</div>
          <div className="text-xs text-muted">Ask anything about this account</div>
        </div>
      </div>

      {/* Thread */}
      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {disabled && (
          <div className="flex h-full flex-col items-center justify-center text-center text-faint">
            <Radar className="mb-2 h-8 w-8 text-ink-300" />
            <p className="text-sm">Scout unlocks once the brief is ready.</p>
          </div>
        )}

        {!disabled && messages.length === 0 && !mutation.isPending && (
          <div className="flex h-full flex-col items-center justify-center text-center text-faint">
            <Radar className="mb-2 h-8 w-8 text-ink-300" />
            <p className="text-sm font-medium text-muted">Ask Scout a question</p>
            <p className="mt-1 text-xs">
              e.g. "Who led their last round?" or "Best opening line?"
            </p>
          </div>
        )}

        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="flex justify-end">
              <div className="max-w-[92%] rounded-xl rounded-br-[4px] bg-brand-600 px-3.5 py-2.5 text-[13.5px] text-white">
                {m.content}
              </div>
            </div>
          ) : (
            <div key={m.id} className="flex justify-start">
              <div
                className={`max-w-[92%] rounded-xl rounded-bl-[4px] px-3.5 py-2.5 text-[13.5px] ${
                  notGrounded(m)
                    ? "border border-warn/30 bg-[#fdf4e3] text-ink-800"
                    : "bg-[#f2f4f9] text-ink-800"
                }`}
              >
                {notGrounded(m) && (
                  <div className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-warn">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Not in the sources
                  </div>
                )}
                <MarkdownView>{m.content}</MarkdownView>
              </div>
            </div>
          ),
        )}

        {mutation.isPending && (
          <div className="flex justify-start">
            <div className="flex items-center gap-1 rounded-xl rounded-bl-[4px] bg-[#f2f4f9] px-4 py-3">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-faint [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-faint [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-faint" />
            </div>
          </div>
        )}
      </div>

      {/* Composer */}
      <div className="border-t border-line p-3">
        <div className="flex items-end gap-2">
          <textarea
            className="input max-h-32 min-h-[42px] resize-none py-2.5"
            rows={1}
            placeholder={disabled ? "Waiting for the brief…" : "Ask Scout…"}
            value={input}
            disabled={disabled || mutation.isPending}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button
            className="btn-primary h-[42px] px-4"
            disabled={disabled || mutation.isPending || !input.trim()}
            onClick={send}
            aria-label="Send"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
