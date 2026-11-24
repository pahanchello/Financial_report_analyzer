import os
import requests
from typing import List, Dict
from dotenv import load_dotenv

from .retriever import search_chunks

load_dotenv()

def generate_rag_response(query: str, chunks: List[Dict]) -> str:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct-q4_K_M")

    context_text = "" 
    for i, chunk in enumerate(chunks):
        context_text += f"[{i+1}] {chunk['ticker']} ({chunk['fiscal_year']}), {chunk['section_title']}:\n{chunk['text']}\n\n"

    system_prompt = """You are an expert financial analyst assistant. 
Your task is to answer the user's question based *strictly* on the provided context.

Rules:
1. Use ONLY the information provided in the context. Do NOT make up facts or use outside knowledge.
2. If the context does not contain the answer, state clearly: "I cannot find this information in the provided documents."
3. Always cite your sources using the bracketed numbers provided in the context (e.g., [1], [2]) at the end of the relevant sentences.
4. Keep the answer concise, professional, and directly address the question.
5. If the question is about financial figures, provide the exact numbers and years mentioned in the context."""

    user_prompt = f"Context:\n{context_text}\n\nQuestion:{query}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content":system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream":False,
        "options": {
            "temperature": 0.1,
            "num_predict": 600,
            
        }
    }

    print(f"\n Generating reponse using {model} (this may take 10-30 seconds)")
    response = requests.post(f"{host}/api/chat", json = payload, timeout = 120)
    response.raise_for_status()

    result= response.json()
    return result["message"]["content"]

def test_full_rag_pipeline():
    test_queries = [
        {
            "query": "What was Apple's iPhone net sales in 2026?",
            "ticker": "AAPL",
            "year": 2026
        },
        {
            "query": "How did tariffs impact the supply chain?",
            "ticker": "AAPL",
            "year": 2026
        }
    ]

    for test in test_queries:
        print('\n' + '='*80)
        print(f" USER QUERY: '{test['query']}'")
        print(f"  (Filter: {test['ticker']}, {test['year']})")
        print("="*80)  

        chunks = search_chunks(query=test['query'], top_k=3, ticker_filter=test['ticker'], year_filter = test['year'])
        if not chunks:
            print('No relevant chunks found')
            continue

        answer = generate_rag_response(test['query'], chunks)
        print("\nAI ANSWER:")
        print("-" * 80)
        print(answer)
        print("-" * 80)
        
if __name__ == "__main__":
    test_full_rag_pipeline()  