from typing import BinaryIO

from pypdf import PdfReader


def extract_text_from_pdf(pdf_file: BinaryIO) -> list[dict[str, int | str]]:
    """Extract text page by page from an uploaded PDF file."""
    reader = PdfReader(pdf_file)

    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page_number": page_number, "text": text.strip()})

    return pages

def split_text_into_chunks(
    pages: list[dict[str, int | str]],
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[dict[str, int | str]]:
    """Combine page text and split it into overlapping chunks."""

    full_text = "\n\n".join(str(page["text"]) for page in pages)

    chunks = []
    start = 0
    chunk_id = 1

    while start < len(full_text):
        end = start + chunk_size
        chunk_text = full_text[start:end].strip()

        if chunk_text:
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
            })

        if end >= len(full_text):
            break

        start = end - overlap
        chunk_id += 1

    return chunks