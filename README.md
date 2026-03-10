# 🤖 AI Document Intelligence Platform

A cross-platform AI orchestration hub that intelligently routes business documents through multiple AI providers — **Groq**, **Claude**, and **Gemini** — each handling the task it does best.

## 🎯 What It Does

Upload any business document and the platform automatically:

| Task | Provider | Why |
|------|----------|-----|
| ⚡ Key Facts Extraction | Groq (Llama) | Speed |
| 📝 Executive Summary | Groq (Llama) | Speed |
| 🧠 Deep Analysis | Claude | Reasoning depth |
| 😊 Sentiment & Tone | Claude | Language understanding |
| ✨ Context Enrichment | Gemini | Broad knowledge |
| ❓ Smart Questions | Gemini | Creative synthesis |

All tasks run **in parallel** — full report in seconds.

## 🖥️ Screenshots

### Main Interface
Upload a document → select tasks → run orchestrated analysis across 3 AI providers

### Analytics Dashboard
Track usage, latency, and token consumption across all providers over time

## 🚀 Quick Start

### 1. Clone
```bash
git clone https://github.com/neelimasap/ai-orchestration-hub.git
cd ai-orchestration-hub
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up API keys
```bash
cp .env.example .env
# Edit .env with your keys
```

### 4. Run
```bash
streamlit run app.py
```

Open `http://localhost:8501`

## 🔑 API Keys Needed

| Provider | Get Key From | Free Tier |
|----------|-------------|-----------|
| Groq | [console.groq.com](https://console.groq.com) | ✅ Generous |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | Paid |
| Google | [aistudio.google.com](https://aistudio.google.com) | ✅ Free |

## 📁 Project Structure

```
ai-orchestration-hub/
├── app.py                  # Main Streamlit app
├── pages/
│   └── 2_Analytics.py      # Usage analytics dashboard
├── core/
│   ├── providers.py        # Groq / Claude / Gemini abstraction layer
│   └── database.py         # SQLite logging & stats
├── .env.example            # API key template
└── requirements.txt
```

## ✨ Features

- **Multi-provider orchestration** — routes tasks to the best AI for the job
- **Parallel execution** — all tasks run simultaneously via ThreadPoolExecutor
- **Automatic fallback** — if Gemini is rate-limited, falls back to Groq automatically
- **Analytics dashboard** — track latency, token usage, and provider performance
- **Full report download** — export complete analysis as Markdown
- **Supports PDF, DOCX, TXT** documents

## 🛠️ Tech Stack

- **UI**: Streamlit
- **LLMs**: Groq (Llama 3.3), Anthropic (Claude), Google (Gemini)
- **Storage**: SQLite
- **Charts**: Altair
- **Async**: ThreadPoolExecutor for parallel model calls

## 📄 License

MIT
