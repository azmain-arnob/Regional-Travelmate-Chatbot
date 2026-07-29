import os
import re
import time
import psutil
import torch

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ---------------------------------------------------------------------------
# Shared state. app.py imports this dict and injects the text-generation
# pipeline and BASIC_RESPONSES into it after the model loads.
# ---------------------------------------------------------------------------
app_state = {
    "hf_pipeline": None,      # set by app.py
    "BASIC_RESPONSES": {},    # set by app.py
    "vector_store": None,     # built from uploaded documents
    "embeddings": None,       # cached embedding model
    "last_files": None,       # signature of the last processed files
    "feedback": {"accurate": 0, "inaccurate": 0},
}

HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
_start_time = time.time()


def _get_embeddings():
    """Load the embedding model once, then reuse it (faster on repeat calls)."""
    if app_state.get("embeddings") is None:
        app_state["embeddings"] = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return app_state["embeddings"]


def _normalize_files(files):
    """Gradio may pass None, a single path, or a list of paths/file objects.
    Return a clean list of file-path strings."""
    if not files:
        return []
    if not isinstance(files, (list, tuple)):
        files = [files]
    paths = []
    for f in files:
        if f is None:
            continue
        paths.append(getattr(f, "name", f))  # object -> .name, else the string
    return paths


def _build_vector_store(file_paths):
    """Load all uploaded PDF/DOCX files, split them, build a Chroma store."""
    all_docs = []
    for path in file_paths:
        lower = str(path).lower()
        if lower.endswith(".pdf"):
            loader = PyPDFLoader(path)
        elif lower.endswith(".docx"):
            loader = Docx2txtLoader(path)
        else:
            continue  # skip unsupported files instead of crashing
        all_docs.extend(loader.load())

    if not all_docs:
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(all_docs)
    return Chroma.from_documents(chunks, _get_embeddings())


def _clean_answer(text):
    """Strip the model's <think> reasoning and leftover prompt scaffolding."""
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.replace("<think>", "").replace("</think>", "")
    if "Answer:" in text:
        text = text.split("Answer:")[-1]
    return text.strip()


def chat_with_documents(query, files):
    """Main chatbot handler. Signature MUST match app.py: (query, files)."""
    query = (query or "").strip()
    if not query:
        return "Please type a question first."

    # 1) Canned replies for simple greetings
    basic = app_state.get("BASIC_RESPONSES", {})
    if query.lower() in basic:
        return basic[query.lower()]

    # 2) (Re)build the vector store only when new files are uploaded
    file_paths = _normalize_files(files)
    if file_paths:
        signature = tuple(sorted(file_paths))
        if signature != app_state.get("last_files"):
            app_state["vector_store"] = _build_vector_store(file_paths)
            app_state["last_files"] = signature

    vector_store = app_state.get("vector_store")
    if vector_store is None:
        return "Please upload a PDF or DOCX document first, then ask your question."

    # 3) Retrieve context
    docs = vector_store.similarity_search(query, k=3)
    context = "\n".join(d.page_content for d in docs)

    # 4) Generate the answer using the pipeline injected by app.py
    pipe = app_state.get("hf_pipeline")
    if pipe is None:
        return "The language model is not loaded yet. Please wait and try again."

    prompt = (
        "You are a helpful travel assistant. Use ONLY the context below to answer.\n\n"
        f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    )

    try:
        result = pipe(
            prompt,
            max_new_tokens=512,
            do_sample=False,
            return_full_text=False,
            truncation=True,
        )
        generated = result[0]["generated_text"]
    except Exception as e:
        return f"Sorry, something went wrong while generating the answer: {e}"

    answer = _clean_answer(generated)
    return answer or "I could not find an answer in the uploaded document(s)."


# ---------------------------------------------------------------------------
# Feedback handlers wired to the 👍 / 👎 buttons in app.py
# ---------------------------------------------------------------------------
def on_feedback_accurate():
    app_state["feedback"]["accurate"] += 1
    return "Thanks for your feedback! Marked as **accurate**."


def on_feedback_inaccurate():
    app_state["feedback"]["inaccurate"] += 1
    return "Thanks for your feedback! Marked as **inaccurate**. We'll improve."


# ---------------------------------------------------------------------------
# Performance report (imported by app.py). Returns a markdown STRING.
# ---------------------------------------------------------------------------
def get_performance_report():
    process = psutil.Process()
    ram_mb = process.memory_info().rss / (1024 * 1024)
    uptime = time.time() - _start_time
    fb = app_state.get("feedback", {"accurate": 0, "inaccurate": 0})
    total = fb["accurate"] + fb["inaccurate"]
    acc_rate = (fb["accurate"] / total * 100) if total else 0.0
    gpu = "Available" if torch.cuda.is_available() else "Not available"
    return (
        "### Performance Summary\n"
        f"- **RAM Usage:** {ram_mb:.2f} MB\n"
        f"- **Uptime:** {uptime:.1f} seconds\n"
        f"- **CPU Utilization:** {psutil.cpu_percent(interval=None)} %\n"
        f"- **GPU:** {gpu}\n"
        f"- **Feedback:** accurate {fb['accurate']} | inaccurate {fb['inaccurate']} "
        f"(accuracy {acc_rate:.0f}%)\n"
    )
