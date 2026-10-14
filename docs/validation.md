# Local validation

Validated on 2026-10-14 with Python 3.12.14, Streamlit 1.65.0, and pypdf 6.20.1 on Linux.

| Check | Observed result |
| --- | --- |
| `python -m unittest discover -s tests -v` | 24 tests passed |
| `python -m evals.run_retrieval` | Expected evidence retrieved within top 4 for 7/7 positive smoke cases; no overlap for 3/3 negative smoke cases |
| Persian terminal retrieval | Annual-leave passage returned first with the original Persian text |
| UI interaction tests | Example loading, question submission, language switch, empty selection, removal, and session clear passed |
| Ollama adapter tests | Mocked transport and source/quote validation passed |
| Editable package installation | `pip install -e .` built and installed successfully |

No live Ollama model was installed or called. Model quality, RAM requirements, token speed, and real model compatibility have not been measured. An application screenshot review has not been performed. GitHub Actions is configured but has not run on a remote repository.

The smoke set is deliberately small and uses the bundled fictional handbooks. It is not held out and contains easy zero-overlap negatives. The counts above must not be reported as general answer accuracy, multilingual semantic performance, or hallucination prevention. Build a separate reviewed set of real questions before making quality claims.

The exact dependency snapshot is in `requirements.snapshot.txt`.
