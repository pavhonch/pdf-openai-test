import re
from pathlib import Path

import fitz


class PdfExtractError(Exception):
    pass


def extract_pdf_text(path: Path) -> tuple[str, int]:
    doc: fitz.Document | None = None
    parts: list[str] = []
    try:
        try:
            doc = fitz.open(path)
        except Exception:
            raise PdfExtractError(
                "Could not open this PDF. The file may be corrupt or not a real PDF."
            ) from None

        try:
            for i, page in enumerate(doc, start=1):
                try:
                    raw = page.get_text() or ""
                except Exception:
                    raise PdfExtractError(
                        f"Could not read text from page {i}. The PDF may be corrupt."
                    ) from None
                raw = raw.replace("\r", "")
                parts.append(raw.strip())
            page_count = len(doc)
        except PdfExtractError:
            raise
        except Exception:
            raise PdfExtractError(
                "Could not read this PDF. The file may be corrupt or use an unsupported layout."
            ) from None
    finally:
        if doc is not None:
            doc.close()

    text = "\n\n".join(parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if page_count == 0:
        raise PdfExtractError("This PDF has no pages.")

    if len(text) < 80:
        raise PdfExtractError(
            "Almost no text could be extracted. The PDF may be scanned or "
            "image-only; OCR is not supported."
        )

    if page_count >= 2 and len(text) // page_count < 35:
        raise PdfExtractError(
            "Very little text per page. Image-heavy or scanned PDFs often "
            "produce empty or unreliable text extraction."
        )

    return text, page_count
