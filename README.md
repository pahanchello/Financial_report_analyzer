# 📊 Financial Report Analyzer

A local, fully free **RAG (Retrieval-Augmented Generation)** system that turns SEC 10-K annual reports into a question-answering financial assistant with source citations. No API keys, no cloud costs — everything runs on your own machine.

## What it does

You ask a question in plain English, e.g. *"How did tariffs impact Apple's supply chain?"*, and the system:
1. Converts the question into a 768-dim vector (`nomic-embed-text` via Ollama)
2. Searches a Qdrant vector database of report chunks, optionally filtered by ticker / fiscal year / section
3. Passes the top-k chunks to a local LLM (`Qwen2.5-7B-Instruct`, 4-bit quantized)
4. Returns an answer with citations `[1]`, `[2]` pointing to the exact source chunks

If the retrieved context does not contain the answer, the model is instructed to say *"I cannot find this information in the provided documents"* instead of hallucinating.

## Pipeline
SEC EDGAR (HTML) → Parser → Sections → Chunker → Embeddings → Qdrant → Retriever → LLM → Answer + citations

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | `Qwen2.5-7B-Instruct-Q4_K_M` (Ollama) |
| Embeddings | `nomic-embed-text` (768 dimensions) |
| Vector DB | `Qdrant` (Docker) |
| Parsing | `BeautifulSoup4`, `lxml` |
| Backend | Python 3.10+ |

## 📚 Dataset

Real SEC 10-K annual reports from [SEC EDGAR](https://www.sec.gov/edgar):

| Company | Ticker | Fiscal Year | Chunks |
|---------|--------|-------------|--------|
| Apple Inc. | AAPL | 2026 | 181 |
| Alphabet Inc. | GOOGL | 2025 | 271 |
| Microsoft Corp. | MSFT | 2024 | 259 |
| **Total** | | | **711** |

## 🚀 Installation

### Prerequisites
- Python 3.10+, Docker, Ollama ([download](https://ollama.com/download))
- 8GB+ RAM, 8GB+ VRAM

### Setup

```bash
git clone https://github.com/yourusername/financial-report-analyzer.git
cd financial-report-analyzer

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env

# Install Ollama models
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct-q4_K_M

# Start Qdrant
docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage --name qdrant qdrant/qdrant
