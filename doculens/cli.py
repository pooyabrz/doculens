"""Inspect retrieval from the terminal: python -m doculens.cli FILE --question TEXT."""

import argparse
from pathlib import Path

from doculens.documents import DocumentError, load_document
from doculens.retrieval import BM25Index


def main() -> None:
    parser = argparse.ArgumentParser(description="Find source passages with DocuLens.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--question", required=True)
    parser.add_argument("--top-k", type=int, default=4, choices=range(1, 11))
    args = parser.parse_args()
    try:
        documents = [load_document(path.name, path.read_bytes()) for path in args.files]
    except (DocumentError, OSError) as exc:
        parser.error(str(exc))
    hits = BM25Index([chunk for doc in documents for chunk in doc.chunks]).search(
        args.question, args.top_k
    )
    if not hits:
        print("No matching passage found. This is lexical search, not an answerability judgment.")
    for number, hit in enumerate(hits, start=1):
        page = f", page {hit.chunk.page}" if hit.chunk.page is not None else ""
        print(f"[{number}] {hit.chunk.filename}{page}, passage {hit.chunk.passage}")
        print(hit.chunk.text + "\n")


if __name__ == "__main__":
    main()
