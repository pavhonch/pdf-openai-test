import type { DocumentRecord } from "./types";

const apiBase =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

type ErrorBody = {
  detail?: unknown;
};

function detailMessage(detail: unknown): string | null {
  if (detail == null) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const first = detail[0];
    if (first && typeof first === "object" && "msg" in first) {
      return String((first as { msg: unknown }).msg);
    }
    return JSON.stringify(detail);
  }
  if (typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message);
  }
  return JSON.stringify(detail);
}

async function readApiError(res: Response): Promise<string> {
  const text = await res.text();
  if (!text) return res.statusText;
  try {
    const body = JSON.parse(text) as ErrorBody;
    return detailMessage(body.detail) ?? res.statusText;
  } catch {
    return text;
  }
}

export async function fetchDocuments(): Promise<DocumentRecord[]> {
  const res = await fetch(`${apiBase}/api/documents`);
  if (!res.ok) throw new Error(await readApiError(res));
  return res.json() as Promise<DocumentRecord[]>;
}

export async function uploadPdf(file: File): Promise<DocumentRecord> {
  const body = new FormData();
  body.append("file", file);
  const res = await fetch(`${apiBase}/api/documents`, {
    method: "POST",
    body,
  });
  if (!res.ok) throw new Error(await readApiError(res));
  return res.json() as Promise<DocumentRecord>;
}

export async function fetchDocument(
  id: number,
): Promise<DocumentRecord> {
  const res = await fetch(`${apiBase}/api/documents/${id}`);
  if (!res.ok) throw new Error(await readApiError(res));
  return res.json() as Promise<DocumentRecord>;
}
