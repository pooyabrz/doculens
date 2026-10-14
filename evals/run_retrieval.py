"""Small lexical retrieval smoke set; not a general RAG-quality benchmark."""

import json
from pathlib import Path

from doculens.documents import load_document
from doculens.retrieval import BM25Index


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    documents = [load_document(path.name, path.read_bytes()) for path in sorted((root / "examples").glob("*.md"))]
    index = BM25Index([chunk for document in documents for chunk in document.chunks])
    cases = json.loads((root / "evals" / "questions.json").read_text(encoding="utf-8"))
    positives, positive_hits, negatives, zero_overlap = 0, 0, 0, 0
    for case in cases:
        hits = index.search(case["question"], top_k=4)
        if case["expected_quote"] is None:
            negatives += 1
            passed = not hits
            zero_overlap += int(passed)
        else:
            positives += 1
            passed = any(case["expected_quote"] in hit.chunk.text for hit in hits)
            positive_hits += int(passed)
        print(f"{'PASS' if passed else 'FAIL'} | {case['question']}")
    print(json.dumps({
        "positive_evidence_hit_at_4": f"{positive_hits}/{positives}",
        "zero_overlap_negative_cases": f"{zero_overlap}/{negatives}",
        "scope": "10 curated smoke cases; no LLM calls, no cross-language or semantic evaluation",
    }, ensure_ascii=False, indent=2))
    if positive_hits != positives or zero_overlap != negatives:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
