# Development roadmap

Advance when a milestone's behavior can be demonstrated. Keep sample fixtures separate from a later held-out evaluation set.

| Milestone | Work | Exit criterion |
| --- | --- | --- |
| v0.1 — current starter | Python UI, document parsing, lexical retrieval, source display, optional Ollama adapter | Run the fictional sample and inspect its evidence; local checks pass |
| v0.2 — semantic retrieval | Choose a multilingual embedding model; add a retriever interface and persistent index | Compare lexical and semantic retrieval on manually labeled real questions, including paraphrases and cross-language cases |
| v0.3 — evaluated generation | Choose a model by budget/hardware; review claim support and no-answer cases | Report evidence recall, claim support, refusal behavior, latency, and measured cost on a held-out set |
| v0.4 — hybrid retrieval | Combine lexical and semantic results; optionally add reranking | Keep the change only if measured quality justifies its latency and complexity |
| v0.5 — service layer | FastAPI, PostgreSQL/pgvector, background jobs, document lifecycle | Restart without losing the corpus; job failures and deletions are recoverable |
| v0.6 — product UI | Separate web frontend when needed; source viewer, upload progress, accessible states | Demonstrate upload-to-answer flow and verify source navigation |
| v1.0 — public portfolio release | Authentication and isolation for uploads, Docker, CI, demo video, reproducible evaluation | A new reviewer can run it, inspect results and limitations, and reproduce the demo |

## Immediate exercise

1. Run the Streamlit example without a model.
2. Read `models.py`, `documents.py`, and `retrieval.py`.
3. Select three suitable text PDFs.
4. Write seven answerable and three unanswerable questions with manual source labels.
5. Record paraphrases that BM25 misses.
6. Choose cloud or local models using available budget and RAM/GPU information.

## Later options

OCR, table-aware parsing, comparison of document versions, conflict detection, saved notes, batch questions, and local-only deployment are separate extensions. Select them according to the chosen use case and evaluate their new failure modes.

Avoid adding multiple databases, agent orchestration, fine-tuning, or a complex frontend before a measured requirement calls for them.
