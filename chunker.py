"""
Stage 2 of the pipeline: splitting documents into chunks.
"""

from dataclasses import dataclass

import config
from ingest import Document


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents on '##' markdown section headers.

    These guides are hand-structured into sections (Getting there, Eat and
    drink, Where to stay, etc.) that are each a complete, self-contained
    thought. Splitting on those boundaries instead of a fixed character count
    keeps each chunk answerable on its own, and avoids cutting a section in
    half or merging two unrelated ones together.

    Each chunk is prefixed with the document's title (the '#' line) so that,
    read alone, it's still clear which place/topic it's about.
    """
    chunks: list[Chunk] = []

    for doc in documents:
        lines = doc.text.splitlines()

        title = ""
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        sections: list[list[str]] = []
        current: list[str] = []
        for line in lines:
            if line.startswith("# ") and not line.startswith("## "):
                continue  # skip the title line — it's already saved above
            if line.startswith("## "):
                if current:
                    sections.append(current)
                current = [line]
            else:
                current.append(line)
        if current:
            sections.append(current)

        index = 0
        for section_lines in sections:
            body = "\n".join(section_lines).strip()
            if not body:
                continue

            text = f"{title}\n\n{body}" if title else body

            chunks.append(
                Chunk(
                    text=text,
                    source=doc.source,
                    index=index,
                    produced_by="chunker.py::split_documents",
                )
            )
            index += 1

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))