from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    id: str
    document_id: str
    filename: str
    text: str
    passage: int
    page: int | None = None


@dataclass(frozen=True)
class Document:
    id: str
    filename: str
    chunks: tuple[Chunk, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SearchHit:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Citation:
    chunk: Chunk
    quote: str


@dataclass(frozen=True)
class Claim:
    text: str
    citations: tuple[Citation, ...]


@dataclass(frozen=True)
class Answer:
    status: str
    claims: tuple[Claim, ...]
