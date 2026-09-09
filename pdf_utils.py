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

