from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from typing import Iterable, Optional

import fitz  # PyMuPDF


@dataclass(frozen=True)
class PdfExtractResult:
    text: str
    page_count: int
    used_ocr_or_vision_needed: bool


def extract_text_fast(pdf_path: str) -> PdfExtractResult:
    doc = fitz.open(pdf_path)
    try:
        texts: list[str] = []
        for page in doc:
            texts.append(page.get_text("text") or "")
        full = "\n".join(t.strip() for t in texts if t is not None).strip()
        # Heuristic: very short output means it's likely scanned or extraction failed.
        needs_fallback = len(full) < 800
        return PdfExtractResult(
            text=full,
            page_count=doc.page_count,
            used_ocr_or_vision_needed=needs_fallback,
        )
    finally:
        doc.close()


def render_pages_as_png_b64(
    pdf_path: str,
    *,
    max_pages: int = 10,
    zoom: float = 2.0,
    page_indices: Optional[Iterable[int]] = None,
) -> list[str]:
    """
    Renders pages to PNG and returns base64 strings (no data: prefix).
    """
    doc = fitz.open(pdf_path)
    try:
        if page_indices is None:
            page_indices = range(min(max_pages, doc.page_count))
        mat = fitz.Matrix(zoom, zoom)
        out: list[str] = []
        for i in page_indices:
            page = doc.load_page(int(i))
            pix = page.get_pixmap(matrix=mat, alpha=False)
            png_bytes = pix.tobytes("png")
            out.append(base64.b64encode(png_bytes).decode("ascii"))
        return out
    finally:
        doc.close()

