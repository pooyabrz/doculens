# DocuLens

A Python-first document Q&A prototype with inspectable evidence.

**Status: v0.1 learning milestone.** The default mode retrieves source passages with BM25 and makes no model calls. An optional Ollama adapter generates answers with validated source IDs and verbatim quotes. Semantic retrieval, persistent storage, and public deployment are future milestones.

[راهنمای فارسی](README.fa.md) · [Architecture](docs/architecture.md) · [Roadmap](docs/roadmap.md) · [Validation](docs/validation.md)

## What works today

| Feature | Behavior |
| --- | --- |
| Documents | Text PDFs, UTF-8 TXT, and Markdown; multiple files per session |
| Sources | Physical PDF page numbers and passage numbers; text files use passages |
| Retrieval | Transparent BM25 baseline, Persian/Arabic letter and digit normalization |
| Scope | Search only the documents selected in the sidebar |
| Evidence mode | Matching source text, clearly labeled as evidence rather than an AI answer |
| Optional generation | Ollama structured output; unknown sources and fabricated quotes are rejected |
| Session management | Remove documents, clear the conversation, export Markdown |
| Interface | Persian and English labels |

This starter uses only two direct dependencies: Streamlit and pypdf. The core modules do not import Streamlit, so they can later be reused behind FastAPI.

## Quick start

Use Python **3.12** for the tested environment. The project declares support for Python 3.11–3.14. Extract the archive and open a terminal in its `doculens` folder.

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS / Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

Open http://localhost:8501 if a browser does not open automatically. Click **Load example documents**, keep **Evidence only** selected, and ask:

```text
How many annual leave days are available?
```

The annual-leave passage should contain **24 days**. In the Persian interface, ask `مرخصی سالانه چند روز است؟`. The sample handbooks are fictional and included under this repository's MIT license.

Installing dependencies requires internet access. After installation, evidence mode needs no API key, model download, or model service. Stop the app with `Ctrl+C`.

## Optional Ollama generation

1. Install Ollama from its official website and start its local server.
2. Download a model appropriate for your RAM, GPU, and language needs. Check its license. This starter deliberately does not select or download a model for you.
3. Verify that your model appears in `ollama list`.
4. Select **Answer with Ollama** and enter the exact installed model name.
5. Ask the same test question. Inspect each answer claim and its supporting quote.

The adapter uses `http://localhost:11434/api/chat`, structured JSON output, and a 45-second timeout. A cold or large model can exceed that timeout; evidence mode remains usable. Test your chosen model's JSON-schema support and answer quality before relying on it.

The app sends the question and retrieved passages to your local Ollama server. If you use an Ollama cloud model, that server may forward the content to its provider. For a local-only setup, use a downloaded local model and configure Ollama accordingly. The starter makes no cloud API calls itself.

`OLLAMA_MODEL` may supply the initial model name. `.env.example` documents this optional variable; `.env` files are **not automatically loaded**. Entering the name in the sidebar requires no environment configuration.

Source validation proves that the cited passage and quoted text exist. It does **not** prove that the quote supports the generated claim, that every relevant passage was retrieved, or that document instructions cannot influence a model. Human-reviewed evaluation is the next quality milestone. Each question is standalone; previous chat messages are displayed but are not sent as conversational context.

## Run the checks

Replace `python` below with the virtual environment's Python executable from the quick-start commands:

```bash
python -m unittest discover -s tests -v
python -m evals.run_retrieval
python -m doculens.cli examples/team_handbook_en.md --question "annual leave days"
```

The tests include a real in-memory PDF fixture, source filtering, Persian normalization, citation rejection, a mocked Ollama transport, and Streamlit interaction tests. They make no live model calls. The ten-question retrieval set is a small curated smoke check; its results are not a general accuracy score or evidence of cross-language retrieval quality.

`requirements.snapshot.txt` records the complete Python 3.12/Linux environment used for local validation. `requirements.txt` pins the two direct dependencies; transitive versions may resolve differently on other platforms. GitHub Actions is configured for Python 3.11 and 3.12 and will execute when the repository is pushed.

## Project layout

| Path | Responsibility |
| --- | --- |
| `app.py` | Streamlit UI, per-session documents and history |
| `doculens/documents.py` | Validation, extraction, chunking, source locations |
| `doculens/retrieval.py` | BM25 indexing and document-scope filtering |
| `doculens/generation.py` | Ollama transport and output validation |
| `doculens/models.py` | Shared immutable data objects |
| `doculens/cli.py` | Terminal evidence inspection |
| `examples/` | Fictional Persian and English handbooks |
| `evals/` | Retrieval smoke questions and runner |
| `tests/` | Core and interface checks |
| `docs/` | Architecture, validation, development roadmap |

## Limits of v0.1

- BM25 matches words, not meanings. An English question may not retrieve Persian-only evidence. Word forms and paraphrases can be missed.
- A matching passage does not establish that the question is answerable. No-match results mean no lexical overlap, not proof that the answer is absent.
- Image-only PDFs need OCR. Mixed PDFs generate warnings for pages without extractable text.
- PDF reading order, complex tables, diagrams, and exact on-page highlighting are not supported reliably.
- Up to 10 MiB per file, 200 PDF pages, 20 documents, and 4,000 passages per session. Limits reduce routine load but are not an isolation boundary for hostile PDFs.
- Extraction is synchronous. Persistent storage, background workers, authentication, and multi-user operation are not implemented.
- Uploaded content stays in the browser session's server memory; closing or reloading the session can lose it. Uploads are not written to disk or placed in a shared cache. Exporting a conversation explicitly creates a download.
- This configuration binds to localhost. Before accepting public uploads, implement authentication, access controls, isolated parsing, and operational limits.

## Next milestone

Run the sample first, then assemble three suitable text PDFs and ten manually checked questions. Add embeddings behind a retrieval interface and compare that implementation to BM25 using a separate evaluation set. Add FastAPI and a separate web frontend when there is a concrete product need for them.

## License

MIT for this code and the fictional examples. Third-party dependencies and any downloaded model retain their own licenses. See [LICENSE](LICENSE).

## Official references

- [Streamlit installation](https://docs.streamlit.io/get-started/installation/command-line)
- [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest)
- [pypdf text extraction](https://pypdf.readthedocs.io/en/latest/user/extract-text.html)
- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
