"""Extract plain text from PDF, DOCX, or text resumes."""

from io import BytesIO
from pathlib import Path

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".txt", ".md"}


def extract_text(data: bytes, suffix: str) -> str:
    suffix = suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported file type '{suffix}'. Use one of: {', '.join(sorted(SUPPORTED_SUFFIXES))}")

    if suffix == ".pdf":
        from pypdf import PdfReader
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
    elif suffix == ".docx":
        import docx2txt
        text = docx2txt.process(BytesIO(data))
    else:
        text = data.decode("utf-8")

    if not text.strip():
        raise ValueError("Couldn't extract any text from the resume (is it a scanned image PDF?).")
    return text


def load_resume(path: str | Path) -> str:
    path = Path(path)
    return extract_text(path.read_bytes(), path.suffix)
