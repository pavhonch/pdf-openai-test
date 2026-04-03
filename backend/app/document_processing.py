from pathlib import Path

from sqlalchemy.orm import Session

from app.chunking import chunk_text
from app.config import MAX_TOTAL_CHARS, UPLOAD_DIR
from app.database import SessionLocal
from app.llm_client import LLMError
from app.models import Document
from app.pdf_extract import PdfExtractError, extract_pdf_text
from app.summarization import hierarchical_summary

_ERROR_CAP = 500

_BASE_UNEXPECTED = "Processing stopped unexpectedly. Try again or use a different PDF."


def _trim_message(text: str) -> str:
    t = " ".join(text.strip().split())
    if not t:
        return _BASE_UNEXPECTED
    if len(t) > _ERROR_CAP:
        return t[: _ERROR_CAP - 1] + "…"
    return t


def run_document_processing(document_id: int) -> None:
    db: Session = SessionLocal()
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            return

        path = UPLOAD_DIR / f"{document_id}.pdf"
        if not path.is_file():
            doc.status = "failed"
            doc.error_message = "The PDF file is no longer on disk. Try uploading again."
            db.commit()
            return

        doc.status = "processing"
        doc.error_message = None
        db.commit()

        try:
            text, page_count = extract_pdf_text(Path(path))
        except PdfExtractError as e:
            doc.status = "failed"
            doc.summary = None
            doc.page_count = None
            doc.error_message = _trim_message(str(e))
            db.commit()
            return

        doc.page_count = page_count
        db.commit()

        if len(text) > MAX_TOTAL_CHARS:
            doc.status = "failed"
            doc.summary = None
            doc.error_message = (
                f"Extracted text is too long for this demo ({len(text):,} characters; "
                f"limit {MAX_TOTAL_CHARS:,}). Use a shorter document or raise MAX_TOTAL_CHARS "
                "in the server environment."
            )
            db.commit()
            return

        chunks = chunk_text(text)
        if not chunks:
            doc.status = "failed"
            doc.error_message = "No text to summarize after splitting the document."
            db.commit()
            return

        try:
            summary = hierarchical_summary(chunks)
        except LLMError as e:
            doc.status = "failed"
            doc.error_message = _trim_message(str(e))
            db.commit()
            return
        except Exception as e:  # noqa: BLE001
            doc.status = "failed"
            doc.error_message = _trim_message(str(e))
            db.commit()
            return

        doc.summary = summary
        doc.status = "done"
        doc.error_message = None
        db.commit()
    except Exception as exc:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass
        try:
            doc_fail = db.get(Document, document_id)
            if doc_fail is not None and doc_fail.status not in ("done", "failed"):
                doc_fail.status = "failed"
                doc_fail.error_message = _trim_message(str(exc))
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
