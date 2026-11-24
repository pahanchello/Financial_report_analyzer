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
## Tech stack

| Layer | Tool |
|---|---|
| LLM & embeddings | Ollama (`qwen2.5:7b-instruct-q4_K_M`, `nomic-embed-text`) |
| Vector database | Qdrant (Docker) |
| Parsing | BeautifulSoup4 + lxml |
| Language | Python 3.10+ |

Runs on modest hardware: ~4.5 GB VRAM for the LLM, ~270 MB for embeddings (tested on 8 GB VRAM / 8 GB RAM).

## Dataset

Real 10-K filings downloaded from [SEC EDGAR](https://www.sec.gov/edgar), split into semantic sections (Item 1 Business, Item 1A Risk Factors, Item 7 MD&A, Item 8 Financial Statements, etc.):

| Company | Ticker | Fiscal year | Sections | Chunks |
|---|---|---|---|---|
| Apple | AAPL | 2026 | 11 | 181 |
| Alphabet | GOOGL | 2025 | 11 | 271 |
| Microsoft | MSFT | 2024 | 11 | 259 |
| **Total** | | | **33** | **711** |

Each chunk is ~1500 characters with 200-character overlap and carries metadata: `ticker`, `fiscal_year`, `period_end`, `item_id`, `section_title`, `chunk_index`.

## Installation
bash
git clone https://github.com/yourusername/financial-report-analyzer.git
cd financial-report-analyzer
python -m venv venv
venv\Scripts\activate # Windows
source venv/bin/activate # Linux / macOS
pip install -r requirements.txt
cp .env.example .env
ollama pull nomic-embed-text
ollama pull qwen2.5:7b-instruct-q4_K_M
docker run -d -p 6333:6333 -p 6334:6334
-v qdrant_storage:/qdrant/storage --name qdrant qdrant/qdrant
**Requirements:** Python 3.10+, Docker, [Ollama](https://ollama.com/download).

