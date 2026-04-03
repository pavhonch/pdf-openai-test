import { useCallback, useEffect, useState } from "react";
import "./App.css";
import { SummaryBody } from "./SummaryBody";
import { fetchDocument, fetchDocuments, uploadPdf } from "./api/client";
import type { DocumentRecord } from "./api/types";

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString();
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function isPollingStatus(status: string): boolean {
  return status === "processing" || status === "uploaded";
}

function statusLabel(status: string): string {
  switch (status) {
    case "uploaded":
      return "Uploaded";
    case "processing":
      return "Processing";
    case "done":
      return "Done";
    case "failed":
      return "Failed";
    default:
      return status;
  }
}

function statusHelp(status: string): string {
  switch (status) {
    case "uploaded":
      return "Waiting for the worker to start.";
    case "processing":
      return "Extracting text and calling the model. This can take a minute on long PDFs.";
    case "done":
      return "Summary is ready below.";
    case "failed":
      return "Something went wrong. See the message below.";
    default:
      return "";
  }
}

export default function App() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [banner, setBanner] = useState<{ kind: "ok" | "err"; text: string } | null>(
    null,
  );
  const [activeId, setActiveId] = useState<number | null>(null);
  const [activeDoc, setActiveDoc] = useState<DocumentRecord | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [pollNonce, setPollNonce] = useState(0);

  const refresh = useCallback(async () => {
    setLoadError(null);
    try {
      const rows = await fetchDocuments();
      setDocuments(rows);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Could not load recent documents.");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (activeId === null) {
      setActiveDoc(null);
      setDetailError(null);
      return;
    }

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    const step = async () => {
      if (cancelled) return;
      try {
        const d = await fetchDocument(activeId);
        if (cancelled) return;
        setDetailError(null);
        setActiveDoc(d);
        try {
          await refresh();
        } catch {
          /* list refresh is best-effort */
        }
        if (!isPollingStatus(d.status)) return;
      } catch (e) {
        if (cancelled) return;
        setDetailError(
          e instanceof Error ? e.message : "Could not load this document.",
        );
        return;
      }
      timeoutId = setTimeout(step, 2500);
    };

    void step();

    return () => {
      cancelled = true;
      if (timeoutId !== undefined) clearTimeout(timeoutId);
    };
  }, [activeId, refresh, pollNonce]);

  async function onUpload(file: File | null) {
    setBanner(null);
    if (!file) return;
    setBusy(true);
    try {
      const doc = await uploadPdf(file);
      setDetailError(null);
      setActiveId(doc.id);
      setActiveDoc(doc);
      setPollNonce((n) => n + 1);
      setBanner({
        kind: "ok",
        text: `Uploaded “${doc.filename}”. It stays selected below while processing.`,
      });
      await refresh();
    } catch (e) {
      setBanner({
        kind: "err",
        text: e instanceof Error ? e.message : "Upload failed.",
      });
    } finally {
      setBusy(false);
    }
  }

  function selectDocument(d: DocumentRecord) {
    setBanner(null);
    setDetailError(null);
    setActiveId(d.id);
    setActiveDoc(d);
    setPollNonce((n) => n + 1);
  }

  function retryDetail() {
    setDetailError(null);
    setPollNonce((n) => n + 1);
  }

  const doneCount = documents.filter((d) => d.status === "done").length;

  return (
    <div className="layout">
      <header className="page-header">
        <h1>PDF Summary</h1>
        <p className="lede">
          Upload a text-based PDF. The app extracts text, summarizes it with OpenRouter,
          and keeps the last five jobs.
        </p>
      </header>

      <section className="panel upload-card" aria-label="Upload">
        <h2 className="panel-title">Upload</h2>
        <form
          className="upload-row"
          onSubmit={(ev) => {
            ev.preventDefault();
            const input = (ev.currentTarget.elements.namedItem(
              "file",
            )as HTMLInputElement) ?? null;
            void onUpload(input?.files?.[0] ?? null);
          }}
        >
          <input
            name="file"
            type="file"
            accept="application/pdf,.pdf"
            required
            disabled={busy}
          />
          <button type="submit" disabled={busy}>
            {busy ? "Uploading…" : "Upload PDF"}
          </button>
        </form>
        {banner ? (
          <div
            className={`banner ${banner.kind === "ok" ? "ok" : "err"}`}
            role="status"
          >
            {banner.text}
          </div>
        ) : null}
      </section>

      {(activeDoc || activeId !== null) && (
        <section className="panel detail-card" aria-label="Active document">
          <div className="panel-head">
            <h2 className="panel-title">
              {activeDoc ? `Document #${activeDoc.id}` : "Document"}
            </h2>
            {activeDoc ? (
              <span className={`status-badge status-${activeDoc.status}`}>
                {statusLabel(activeDoc.status)}
              </span>
            ) : null}
          </div>

          {detailError ? (
            <div className="detail-fetch-error" role="alert">
              <p>{detailError}</p>
              <button type="button" className="btn-secondary" onClick={retryDetail}>
                Retry
              </button>
            </div>
          ) : null}

          {activeDoc ? (
            <>
              <p className="detail-meta">
                <span className="detail-filename">{activeDoc.filename}</span>
                <span className="meta-sep">·</span>
                <span className="muted">{formatSize(activeDoc.file_size)}</span>
                {activeDoc.page_count != null ? (
                  <>
                    <span className="meta-sep">·</span>
                    <span className="muted">{activeDoc.page_count} pages</span>
                  </>
                ) : null}
                <span className="meta-sep">·</span>
                <span className="muted">{formatTime(activeDoc.created_at)}</span>
              </p>
              <p className={`state-note state-note-${activeDoc.status}`}>
                {statusHelp(activeDoc.status)}
              </p>
              {isPollingStatus(activeDoc.status) ? (
                <p className="polling-hint" aria-live="polite">
                  Still working… this page refreshes every few seconds.
                </p>
              ) : null}
              {activeDoc.error_message ? (
                <div className="error-box" role="alert">
                  {activeDoc.error_message}
                </div>
              ) : null}
              {activeDoc.summary ? (
                <div className="summary-block">
                  <h3 className="summary-title">Summary</h3>
                  <div className="summary-surface">
                    <SummaryBody text={activeDoc.summary} />
                  </div>
                </div>
              ) : activeDoc.status === "done" ? (
                <p className="empty inline">No summary text returned.</p>
              ) : null}
            </>
          ) : !detailError ? (
            <p className="muted">Loading document…</p>
          ) : null}
        </section>
      )}

      <section className="panel list-card" aria-label="Recent documents">
        <h2 className="panel-title">Recent uploads</h2>
        <p className="panel-sub">Last five, newest first. Click a row to inspect.</p>
        {loadError ? (
          <p className="banner err" role="alert">
            {loadError}
          </p>
        ) : documents.length === 0 ? (
          <div className="empty-block">
            <p className="empty-title">Nothing here yet</p>
            <p className="empty">
              Upload a PDF above. Finished summaries show a green &ldquo;Done&rdquo;
              badge in the list.
            </p>
          </div>
        ) : (
          <>
            {doneCount === 0 ? (
              <p className="list-hint muted">
                No completed summaries yet—open the active document to watch progress.
              </p>
            ) : null}
            <ul className="doc-list">
              {documents.map((d) => (
                <li key={d.id}>
                  <button
                    type="button"
                    className={
                      "doc-row" + (activeId === d.id ? " doc-row-active" : "")
                    }
                    onClick={() => selectDocument(d)}
                  >
                    <span className="doc-id">#{d.id}</span>
                    <span className="doc-name">{d.filename}</span>
                    <span className={`status-badge sm status-${d.status}`}>
                      {statusLabel(d.status)}
                    </span>
                    <span className="muted doc-meta">{formatSize(d.file_size)}</span>
                    <span className="muted doc-meta">{formatTime(d.created_at)}</span>
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </div>
  );
}
