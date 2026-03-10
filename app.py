"""
AI Document Intelligence Platform
Main entry point — document upload + orchestrated multi-model analysis.
"""
import io
import os
import sys
import concurrent.futures
from pathlib import Path

import docx
import fitz
import streamlit as st

# ── path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── .env loader ───────────────────────────────────────────────────────────────
_env = ROOT / ".env"
if _env.exists():
    with open(_env) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from core.providers import PROVIDERS, call_groq, call_claude, call_gemini
from core.database import init_db, log_run, save_report

init_db()

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Orchestration Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.provider-card {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.5rem;
}
.task-badge {
    background: #f0f2f6;
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 0.8em;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
    st.title("AI Orchestration Hub")
    st.markdown("---")

    st.header("🔑 API Keys")
    for label, env_var, help_text in [
        ("Groq API Key",       "GROQ_API_KEY",      "console.groq.com"),
        ("Anthropic API Key",  "ANTHROPIC_API_KEY", "console.anthropic.com"),
        ("Google API Key",     "GOOGLE_API_KEY",    "aistudio.google.com"),
    ]:
        val = st.text_input(label, type="password",
                            value=os.getenv(env_var, ""),
                            help=f"Get from {help_text}")
        if val:
            os.environ[env_var] = val

    st.markdown("---")
    st.markdown("### 🗺️ Routing Logic")
    st.markdown("""
| Task | Provider | Why |
|------|----------|-----|
| ⚡ Extract | Groq | Speed |
| 🧠 Analyze | Claude | Reasoning |
| ✨ Enrich | Gemini | Context |
    """)

    st.markdown("---")
    st.page_link("pages/2_Analytics.py", label="📊 Analytics Dashboard", icon="📊")

# ── helpers ───────────────────────────────────────────────────────────────────
def extract_text(file) -> str:
    name = file.name.lower()
    mime = file.type or ""
    if mime == "application/pdf" or name.endswith(".pdf"):
        text = ""
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    if name.endswith(".docx") or "wordprocessingml" in mime:
        document = docx.Document(io.BytesIO(file.read()))
        return "\n".join(p.text for p in document.paragraphs)
    return file.read().decode("utf-8", errors="ignore")

def run_task(fn, doc_name, task, prompt, system, model):
    try:
        result = fn(prompt=prompt, system=system, model=model)
        log_run(doc_name, task, result["provider"], result["model"],
                prompt, result["response"],
                result["latency_ms"], result["input_tokens"], result["output_tokens"])
        return result
    except Exception as e:
        return {"provider": "?", "model": model, "response": f"❌ Error: {e}",
                "latency_ms": 0, "input_tokens": 0, "output_tokens": 0}

# ── main UI ───────────────────────────────────────────────────────────────────
st.title("🤖 AI Document Intelligence Platform")
st.markdown("Upload any business document — the platform routes it to the best AI model for each task.")

uploaded = st.file_uploader(
    "Upload a document (PDF, DOCX, TXT)",
    type=None,
    help="Business reports, contracts, emails, research papers, etc."
)

if uploaded:
    doc_text = extract_text(uploaded)
    doc_name = uploaded.name
    word_count = len(doc_text.split())

    col1, col2, col3 = st.columns(3)
    col1.metric("Document", doc_name)
    col2.metric("Words", f"{word_count:,}")
    col3.metric("Characters", f"{len(doc_text):,}")

    with st.expander("📄 Preview document text", expanded=False):
        st.text(doc_text[:2000] + ("..." if len(doc_text) > 2000 else ""))

    st.markdown("---")
    st.subheader("🎯 Select Analysis Tasks")

    col1, col2, col3 = st.columns(3)
    with col1:
        do_extract   = st.checkbox("⚡ Extract Key Facts", value=True, help="Groq — fast structured extraction")
        do_summarize = st.checkbox("📝 Executive Summary", value=True, help="Groq — concise business summary")
    with col2:
        do_analyze   = st.checkbox("🧠 Deep Analysis", value=True, help="Claude — risks, opportunities, insights")
        do_sentiment = st.checkbox("😊 Sentiment & Tone", value=False, help="Claude — emotional tone analysis")
    with col3:
        do_enrich    = st.checkbox("✨ Context Enrichment", value=True, help="Gemini — broader market/industry context")
        do_questions = st.checkbox("❓ Generate Questions", value=False, help="Gemini — smart follow-up questions")

    # Model overrides
    with st.expander("⚙️ Model Settings (optional)"):
        c1, c2, c3 = st.columns(3)
        groq_model   = c1.selectbox("Groq Model",   PROVIDERS["Groq"]["models"])
        claude_model = c2.selectbox("Claude Model",  PROVIDERS["Claude"]["models"])
        gemini_model = c3.selectbox("Gemini Model",  PROVIDERS["Gemini"]["models"])

    doc_snippet = doc_text[:4000]

    if st.button("🚀 Run Orchestrated Analysis", type="primary", use_container_width=True):
        missing = []
        if (do_extract or do_summarize) and not os.getenv("GROQ_API_KEY"):
            missing.append("Groq")
        if (do_analyze or do_sentiment) and not os.getenv("ANTHROPIC_API_KEY"):
            missing.append("Anthropic")
        if (do_enrich or do_questions) and not os.getenv("GOOGLE_API_KEY"):
            missing.append("Google")

        if missing:
            st.error(f"Missing API keys: {', '.join(missing)}. Add them in the sidebar.")
        else:
            tasks = []
            if do_extract:
                tasks.append(("⚡ Key Facts Extraction", call_groq, groq_model,
                    f"Extract all key facts, entities, dates, numbers, and important points from this document as a structured bullet list:\n\n{doc_snippet}",
                    "You are a precise document analyst. Extract facts clearly and concisely."))
            if do_summarize:
                tasks.append(("📝 Executive Summary", call_groq, groq_model,
                    f"Write a concise executive summary (3-5 sentences) of this document for a business audience:\n\n{doc_snippet}",
                    "You are a business analyst. Write clear, professional summaries."))
            if do_analyze:
                tasks.append(("🧠 Deep Analysis", call_claude, claude_model,
                    f"Provide a deep analysis of this document. Cover: key insights, potential risks, opportunities, and strategic implications. Be thorough and specific:\n\n{doc_snippet}",
                    "You are a senior business consultant with expertise in risk analysis and strategy."))
            if do_sentiment:
                tasks.append(("😊 Sentiment & Tone", call_claude, claude_model,
                    f"Analyze the sentiment, tone and language style of this document. Who is the likely author and audience? What emotional signals are present?\n\n{doc_snippet}",
                    "You are a communications expert and linguist."))
            if do_enrich:
                tasks.append(("✨ Context Enrichment", call_gemini, gemini_model,
                    f"Based on this document, provide broader industry context, relevant trends, and how this fits into the current business landscape:\n\n{doc_snippet}",
                    "You are a market research analyst with broad industry knowledge."))
            if do_questions:
                tasks.append(("❓ Smart Questions", call_gemini, gemini_model,
                    f"Generate 8-10 insightful follow-up questions a business executive should ask after reading this document:\n\n{doc_snippet}",
                    "You are a strategic advisor generating questions that drive deeper thinking."))

            results = {}
            progress = st.progress(0, "Starting analysis...")

            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                futures = {
                    executor.submit(run_task, fn, doc_name, label, prompt, system, model): label
                    for label, fn, model, prompt, system in tasks
                }
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    label = futures[future]
                    results[label] = future.result()
                    progress.progress((i + 1) / len(tasks), f"Completed: {label}")

            progress.progress(1.0, "✅ All tasks complete!")
            st.session_state["results"] = results
            st.session_state["doc_name"] = doc_name

            # Save report
            save_report(doc_name,
                results.get("📝 Executive Summary", {}).get("response", "")[:300],
                {k: {"response": v["response"], "provider": v["provider"],
                     "latency_ms": v["latency_ms"]} for k, v in results.items()})

# ── display results ───────────────────────────────────────────────────────────
if "results" in st.session_state:
    results = st.session_state["results"]
    doc_name = st.session_state.get("doc_name", "Document")

    st.markdown("---")
    st.subheader(f"📊 Intelligence Report — {doc_name}")

    # Performance summary
    pcols = st.columns(len(results))
    for i, (label, r) in enumerate(results.items()):
        provider = r.get("provider", "?")
        icon = PROVIDERS.get(provider, {}).get("icon", "🤖")
        pcols[i].metric(
            label=f"{icon} {label.split(' ', 1)[-1][:20]}",
            value=f"{r['latency_ms']}ms",
            delta=f"{r.get('output_tokens', 0)} tokens"
        )

    st.markdown("---")

    # Results
    for label, r in results.items():
        provider = r.get("provider", "?")
        icon = PROVIDERS.get(provider, {}).get("icon", "🤖")
        with st.expander(f"{icon} {label} — via **{provider}** ({r['latency_ms']}ms)", expanded=True):
            st.markdown(r["response"])

    # Full report download
    full_report = f"# AI Intelligence Report: {doc_name}\n\n"
    for label, r in results.items():
        full_report += f"## {label}\n*Provider: {r['provider']} | {r['latency_ms']}ms*\n\n{r['response']}\n\n---\n\n"

    st.download_button(
        "💾 Download Full Report",
        full_report,
        file_name=f"{doc_name}_intelligence_report.md",
        mime="text/markdown",
        use_container_width=True,
    )
