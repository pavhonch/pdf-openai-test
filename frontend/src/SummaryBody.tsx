import type { ReactNode } from "react";

function inlineEmphasis(segment: string, keyPrefix: string): ReactNode[] {
  const parts = segment.split(/\*\*(.+?)\*\*/g);
  return parts.map((p, j) =>
    j % 2 === 1 ? (
      <strong key={`${keyPrefix}-${j}`}>{p}</strong>
    ) : (
      <span key={`${keyPrefix}-${j}`}>{p}</span>
    ),
  );
}

export function SummaryBody({ text }: { text: string }) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let blockKey = 0;

  while (i < lines.length) {
    const raw = lines[i];
    const t = raw.trimEnd();

    if (t.trim() === "") {
      i += 1;
      continue;
    }

    if (t.startsWith("## ")) {
      blocks.push(
        <h4 key={`b-${blockKey++}`} className="summary-heading">
          {inlineEmphasis(t.slice(3), `h-${i}`)}
        </h4>,
      );
      i += 1;
      continue;
    }

    if (t.startsWith("- ") || t.startsWith("* ")) {
      const items: string[] = [];
      while (i < lines.length) {
        const row = lines[i].trimEnd();
        const tr = row.trim();
        if (tr.startsWith("- ") || tr.startsWith("* ")) {
          items.push(tr.slice(2));
          i += 1;
        } else if (tr === "") {
          i += 1;
          break;
        } else {
          break;
        }
      }
      blocks.push(
        <ul key={`b-${blockKey++}`} className="summary-list">
          {items.map((item, k) => (
            <li key={k}>{inlineEmphasis(item, `li-${k}`)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    const paragraphLines: string[] = [t];
    i += 1;
    while (i < lines.length) {
      const next = lines[i].trimEnd();
      if (next.trim() === "") break;
      if (
        next.startsWith("## ") ||
        next.startsWith("- ") ||
        next.startsWith("* ")
      ) {
        break;
      }
      paragraphLines.push(next);
      i += 1;
    }
    const merged = paragraphLines.join(" ");
    blocks.push(
      <p key={`b-${blockKey++}`} className="summary-p">
        {inlineEmphasis(merged, `p-${i}`)}
      </p>,
    );
  }

  return <div className="summary-body">{blocks}</div>;
}
