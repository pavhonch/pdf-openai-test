from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import (
    MAX_UPLOAD_BYTES,
    OPENROUTER_API_KEY,
    OPENROUTER_KEY_MISSING_MESSAGE,
    UPLOAD_DIR,
)
from app.database import get_db
from app.document_processing import run_document_processing
from app.models import Document
from app.schemas import DocumentResponse

router = APIRouter()


async def _read_pdf_bytes(file: UploadFile, max_bytes: int) -> bytes:
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail={"error": "only_pdf", "message": "Only PDF files are accepted."},
        )

    total = 0
    chunks: list[bytes] = []
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail={
                    "error": "file_too_large",
                    "message": f"Maximum upload size is {max_bytes} bytes.",
                },
            )
        chunks.append(chunk)

    data = b"".join(chunks)
    if len(data) == 0:
        raise HTTPException(
            status_code=400,
            detail={"error": "empty_file", "message": "Uploaded file is empty."},
        )
    if not data.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_pdf",
                "message": "File does not look like a valid PDF.",
            },
        )
    return data


@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Document:
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "openrouter_not_configured",
                "message": OPENROUTER_KEY_MISSING_MESSAGE,
            },
        )

    data = await _read_pdf_bytes(file, MAX_UPLOAD_BYTES)
    safe_name = Path(file.filename or "document.pdf").name

    doc = Document(
        filename=safe_name,
        status="uploaded",
        page_count=None,
        file_size=len(data),
        summary=None,
        error_message=None,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    out = UPLOAD_DIR / f"{doc.id}.pdf"
    try:
        out.write_bytes(data)
    except OSError as e:
        doc.status = "failed"
        doc.error_message = f"Could not save the upload to disk: {e}"
        db.commit()
        db.refresh(doc)
        return doc

    background_tasks.add_task(run_document_processing, doc.id)
    return doc


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    q = select(Document).order_by(Document.created_at.desc()).limit(5)
    return list(db.scalars(q).all())


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Document not found."},
        )
    return doc
