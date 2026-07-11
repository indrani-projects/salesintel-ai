import { Children, isValidElement } from "react";
import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";

const CITATION_SPLIT_RE = /(\[S\d+\])/g;
const CITATION_MATCH_RE = /^\[S\d+\]$/;

/** Wrap inline [S#] citation markers in styled chips, recursively over children. */
function withCitations(children: ReactNode): ReactNode {
  return Children.map(children, (child) => {
    if (typeof child === "string") {
      const parts = child.split(CITATION_SPLIT_RE);
      if (parts.length === 1) return child;
      return parts.map((part, i) =>
        CITATION_MATCH_RE.test(part) ? (
          <sup
            key={i}
            className="mx-0.5 rounded bg-brand-50 px-1 text-[0.7em] font-semibold text-brand-700 ring-1 ring-brand-200"
          >
            {part.replace(/[[\]]/g, "")}
          </sup>
        ) : (
          part
        ),
      );
    }
    if (isValidElement(child)) return child;
    return child;
  });
}

// Reused across the block-level elements that can contain citation text.
const citeComponents = {
  p: ({ children }: { children?: ReactNode }) => <p>{withCitations(children)}</p>,
  li: ({ children }: { children?: ReactNode }) => <li>{withCitations(children)}</li>,
  td: ({ children }: { children?: ReactNode }) => <td>{withCitations(children)}</td>,
  strong: ({ children }: { children?: ReactNode }) => (
    <strong>{withCitations(children)}</strong>
  ),
  em: ({ children }: { children?: ReactNode }) => <em>{withCitations(children)}</em>,
};

export function MarkdownView({ children }: { children: string }) {
  return (
    <div className="md">
      <ReactMarkdown components={citeComponents}>{children}</ReactMarkdown>
    </div>
  );
}
