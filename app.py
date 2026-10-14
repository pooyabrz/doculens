"""Python-first UI. Documents and history are scoped to one browser session."""

import os
import time
from pathlib import Path

import streamlit as st

from doculens import __version__
from doculens.documents import DocumentError, load_document
from doculens.generation import GenerationError, OllamaClient
from doculens.retrieval import BM25Index

ROOT = Path(__file__).resolve().parent
MAX_DOCUMENTS = 20
MAX_SESSION_CHUNKS = 4_000
LABELS = {
    "fa": {
        "tagline": "پرسش از اسناد، با شواهد قابل بررسی",
        "workspace": "اسناد این نشست", "upload": "PDF متنی، TXT یا Markdown",
        "add": "افزودن فایل‌ها", "demo": "بارگذاری اسناد نمونه",
        "clear": "پاک کردن اسناد و گفت‌وگو", "remove": "حذف",
        "scope": "جست‌وجو در این اسناد", "mode": "روش پاسخ",
        "search": "نمایش شواهد — بدون مدل", "ollama": "پاسخ با Ollama",
        "model": "نام مدل نصب‌شده در Ollama", "k": "تعداد بخش‌های بازیابی‌شده",
        "docs": "سند", "passages": "بخش متن", "questions": "پرسش",
        "intro": "یک سند بارگذاری کن یا با اسناد نمونه شروع کن.",
        "notice": "حالت نمایش شواهد، بخش‌های مرتبط متن را نشان می‌دهد؛ پاسخ مولد هوش مصنوعی نیست.",
        "local_notice": "بخش‌های بازیابی‌شده به سرور Ollama همین رایانه فرستاده می‌شوند.",
        "placeholder": "پرسشی مستقل از اسناد انتخاب‌شده بنویس…",
        "choose": "برای پرسیدن سؤال، دست‌کم یک سند را انتخاب کن.",
        "no_hits": "با این عبارت، بخش مرتبطی پیدا نشد. ممکن است واژه‌های دیگری لازم باشد.",
        "insufficient": "مدل در بخش‌های بازیابی‌شده، اطلاعات کافی برای پاسخ پیدا نکرد.",
        "evidence": "بخش‌های مرتبط برای بررسی", "sources": "شواهد پاسخ",
        "quote": "نقل‌قول اصلی", "page": "صفحه", "passage": "بخش",
        "working": "در حال بررسی اسناد…", "export": "دانلود گفت‌وگو به‌صورت Markdown",
        "limit": "حداکثر ۲۰ سند و ۴۰۰۰ بخش متن در هر نشست مجاز است.",
        "long": "پرسش باید حداکثر ۲۰۰۰ نویسه داشته باشد.",
        "try": "نمونه: مرخصی سالانه چند روز است؟",
        "session": "اسناد در حافظه این نشست نگهداری می‌شوند و روی دیسک ذخیره نمی‌شوند.",
        "error": "پاسخ نمایش داده نشد؛ اتصال یا اعتبار منابع را بررسی کن.",
        "added": "اسناد آماده شدند.", "duplicate": "این محتوای سند قبلاً بارگذاری شده است.",
        "errors": {
            "unsupported": "قالب فایل پشتیبانی نمی‌شود.",
            "empty": "فایل خالی است.", "too_large": "حداکثر حجم هر فایل ۱۰ MiB است.",
            "invalid_pdf": "فایل PDF معتبر نیست یا قابل خواندن نیست.",
            "encrypted": "PDF دارای رمز پشتیبانی نمی‌شود.",
            "too_many_pages": "حداکثر تعداد صفحات PDF برابر ۲۰۰ است.",
            "too_much_text": "متن استخراج‌شده بیش از حد مجاز است.",
            "too_many_chunks": "تعداد بخش‌های سند بیش از حد مجاز است.",
            "encoding": "فایل متنی را با UTF-8 ذخیره کن.",
            "no_text": "متنی پیدا نشد؛ فایل اسکن‌شده ممکن است به OCR نیاز داشته باشد.",
        },
    },
    "en": {
        "tagline": "Ask your documents. Inspect the evidence.",
        "workspace": "Session documents", "upload": "Text PDF, TXT, or Markdown",
        "add": "Add files", "demo": "Load example documents",
        "clear": "Clear documents and conversation", "remove": "Remove",
        "scope": "Search these documents", "mode": "Answer mode",
        "search": "Evidence only — no model", "ollama": "Answer with Ollama",
        "model": "Installed Ollama model name", "k": "Retrieved passages",
        "docs": "Documents", "passages": "Passages", "questions": "Questions",
        "intro": "Upload a document or start with the example documents.",
        "notice": "Evidence mode shows matching passages; it does not generate an AI answer.",
        "local_notice": "Retrieved passages are sent to the Ollama server on this computer.",
        "placeholder": "Ask a standalone question about the selected documents…",
        "choose": "Select at least one document before asking a question.",
        "no_hits": "No matching passage was found. Try different words.",
        "insufficient": "The model found insufficient evidence in the retrieved passages.",
        "evidence": "Relevant passages to inspect", "sources": "Answer evidence",
        "quote": "Original quote", "page": "page", "passage": "passage",
        "working": "Checking the documents…", "export": "Download conversation as Markdown",
        "limit": "A session supports up to 20 documents and 4,000 passages.",
        "long": "Questions must be at most 2,000 characters.",
        "try": "Example: How many annual leave days are available?",
        "session": "Documents stay in this session's memory and are not saved to disk.",
        "error": "The answer was withheld. Check the connection or source validation.",
        "added": "Documents are ready.", "duplicate": "This document content is already loaded.",
        "errors": {},
    },
}

st.set_page_config(page_title="DocuLens", page_icon="📖", layout="wide")
for key, value in {"documents": {}, "history": [], "upload_epoch": 0}.items():
    if key not in st.session_state:
        st.session_state[key] = value

language = st.sidebar.selectbox("Language / زبان", ["فارسی", "English"], key="language")
lang = "fa" if language == "فارسی" else "en"
t = LABELS[lang]
direction = "rtl" if lang == "fa" else "ltr"
st.markdown(
    "<style>"
    ".block-container{max-width:1120px;padding-top:2.4rem;}"
    "h1{letter-spacing:-0.04em;}"
    f".stMarkdown p,.stText,.stTextInput input{{direction:{direction};}}"
    "</style>", unsafe_allow_html=True,
)


def add_document(filename: str, data: bytes) -> bool:
    document = load_document(filename, data)
    documents = st.session_state.documents
    if document.id in documents:
        st.sidebar.info(t["duplicate"])
        return False
    total = sum(len(doc.chunks) for doc in documents.values()) + len(document.chunks)
    if len(documents) >= MAX_DOCUMENTS or total > MAX_SESSION_CHUNKS:
        st.sidebar.error(t["limit"])
        return False
    documents[document.id] = document
    st.session_state.scope = list(documents)
    return True


def location(chunk) -> str:
    suffix = f"{t['passage']} {chunk.passage}"
    if chunk.page is not None:
        suffix = f"{t['page']} {chunk.page} · {suffix}"
    return f"{chunk.filename} · {suffix}"


def render_record(record: dict) -> None:
    with st.chat_message("user"):
        st.text(record["question"])
    with st.chat_message("assistant"):
        answer = record["answer"]
        if record["error"]:
            st.error(t["error"])
            st.text(record["error"])
        elif answer is not None:
            if answer.status == "not_found":
                st.info(t["insufficient"])
            else:
                for number, claim in enumerate(answer.claims, start=1):
                    st.text(f"{number}. {claim.text}")
                    for citation in claim.citations:
                        with st.expander(location(citation.chunk)):
                            st.caption(t["quote"])
                            st.text(citation.quote)
        elif record["hits"]:
            st.info(t["evidence"])
        else:
            st.info(t["no_hits"])
        for hit in record["hits"]:
            with st.expander(location(hit.chunk)):
                st.text(hit.chunk.text)
        st.caption(f"{record['mode']} · {record['elapsed']:.2f}s")


with st.sidebar:
    st.header(t["workspace"])
    uploads = st.file_uploader(
        t["upload"], type=["pdf", "txt", "md"], accept_multiple_files=True,
        key=f"uploads_{st.session_state.upload_epoch}",
    )
    if st.button(t["add"], disabled=not uploads, key="add_files"):
        for upload in uploads or []:
            try:
                if add_document(upload.name, upload.getvalue()):
                    st.success(t["added"])
            except DocumentError as exc:
                st.error(f"{upload.name}: {t['errors'].get(exc.code, str(exc))}")
    if st.button(t["demo"], key="load_demo"):
        for filename in ("team_handbook_fa.md", "team_handbook_en.md"):
            add_document(filename, (ROOT / "examples" / filename).read_bytes())
    documents = st.session_state.documents
    for doc_id, document in list(documents.items()):
        st.text(document.filename)
        if st.button(t["remove"], key=f"remove_{doc_id}"):
            del documents[doc_id]
            st.session_state.scope = [item for item in st.session_state.get("scope", []) if item != doc_id]
            st.session_state.history = []
            st.rerun()
        for warning in document.warnings[:5]:
            st.warning(warning)
    if st.button(t["clear"], disabled=not documents, key="clear_session"):
        st.session_state.documents = {}
        st.session_state.history = []
        st.session_state.scope = []
        st.session_state.upload_epoch += 1
        st.rerun()
    selected = st.multiselect(
        t["scope"], options=list(documents),
        format_func=lambda doc_id: documents[doc_id].filename,
        key="scope",
    )
    st.divider()
    mode = st.radio(t["mode"], [t["search"], t["ollama"]], key=f"mode_{lang}")
    use_model = mode == t["ollama"]
    model_name = ""
    if use_model:
        model_name = st.text_input(t["model"], value=os.getenv("OLLAMA_MODEL", ""), key="ollama_model")
        st.caption(t["local_notice"])
    top_k = st.slider(t["k"], 1, 6, 4, key="top_k")
    st.caption(t["session"])

st.title("DocuLens")
st.caption(f"v{__version__} · {t['tagline']}")
columns = st.columns(3)
columns[0].metric(t["docs"], len(documents))
columns[1].metric(t["passages"], sum(len(doc.chunks) for doc in documents.values()))
columns[2].metric(t["questions"], len(st.session_state.history))
if not documents:
    st.info(t["intro"])
else:
    st.caption(t["try"])
if not use_model:
    st.info(t["notice"])
if documents and not selected:
    st.warning(t["choose"])

for record in st.session_state.history:
    render_record(record)

question = st.chat_input(t["placeholder"], disabled=not selected, key="question")
if question:
    if len(question.strip()) > 2_000:
        st.error(t["long"])
    elif question.strip():
        start = time.perf_counter()
        chunks = [chunk for document in documents.values() for chunk in document.chunks]
        hits = BM25Index(chunks).search(question, top_k, set(selected))
        answer, error = None, ""
        if use_model:
            with st.spinner(t["working"]):
                try:
                    answer = OllamaClient(model_name).answer(question, hits, lang)
                except GenerationError as exc:
                    error = str(exc)
        record = {
            "question": question.strip(), "hits": hits, "answer": answer,
            "error": error, "elapsed": time.perf_counter() - start,
            "mode": "Ollama" if use_model else "BM25",
        }
        st.session_state.history = (st.session_state.history + [record])[-30:]
        st.rerun()

if st.session_state.history:
    export = ["# DocuLens conversation", ""]
    for record in st.session_state.history:
        export.extend(["## Question", record["question"], "", f"Mode: {record['mode']}", ""])
        if record["error"]:
            export.extend(["Answer withheld: " + record["error"], ""])
        elif record["answer"] is not None:
            if record["answer"].status == "not_found":
                export.extend(["Insufficient evidence in retrieved passages.", ""])
            for claim in record["answer"].claims:
                export.extend([claim.text, ""])
                for citation in claim.citations:
                    export.extend([location(citation.chunk), citation.quote, ""])
        else:
            export.extend(["Evidence only; no generated answer.", ""])
        for hit in record["hits"]:
            export.extend(["### " + location(hit.chunk), hit.chunk.text, ""])
    st.download_button(t["export"], "\n".join(export), "doculens-conversation.md", "text/markdown")
