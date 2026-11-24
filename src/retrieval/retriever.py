import os
from typing import List, Dict
from dotenv import load_dotenv
from qdrant_client import QdrantClient

from .embeddings import get_embedding
from .vector_store import get_qdrant_client

load_dotenv()

def search_chunks(query:str, top_k: int = 5, ticker_filter: str = None, year_filter: int = None,) -> List[Dict]:
    client = get_qdrant_client()
    collection_name = os.getenv('QDRANT_COLLECTION', 'financial_reports_v2')
    print(f'Embedding query: "{query}"')
    query_vector = get_embedding(query)

    must_conditions = []
    if ticker_filter:
        must_conditions.append({"key": "ticker", "match": {"value": ticker_filter.upper()}})
    if year_filter:
        must_conditions.append({"key": "fiscal_year", "match": {"value": year_filter}})
    search_filter = {'must': must_conditions} if must_conditions else None

    print(f'Searchiung in Qdrant (top_k = {top_k})...')
    results = client.search(
        collection_name=collection_name,
        query_vector=('dense', query_vector),
        query_filter=search_filter,
        limit = top_k,
        with_payload=True
    )

    formatted_results = []
    for hit in results:
        payload = hit.payload
        formatted_results.append({
            'score': round(hit.score, 4),
            'ticker': payload.get('ticker'),
            'fiscal_year': payload.get('item_id'),
            'item_id': payload.get('section_title'),
            'section_title': payload.get('section_title'),
            'text': payload.get('text')[:500] + '...' if len(payload.get("text", "")) > 500 else payload.get("text")            
        })
    return formatted_results

def print_search_results(results: List[Dict]):
    print("\n" + "="*80)
    print(f"НАЙДЕНО РЕЗУЛЬТАТОВ: {len(results)}")
    print("="*80)
    
    for i, res in enumerate(results, 1):
        print(f"\n[{i}] Score: {res['score']:.4f} | Ticker: {res['ticker']} ({res['fiscal_year']}) | Item: {res['item_id']}")
        print(f"    Section: {res['section_title']}")
        print(f"    Snippet: {res['text']}")
        print("-" * 80)

def main( ):
    test_queries = [
        {
            "query": "What was Apple's iPhone net sales in 2026?",
            "ticker": "AAPL",
            "year": 2026
        },
        {
            "query": "What are the main cybersecurity risks mentioned?",
            "ticker": "MSFT",
            "year": 2024
        },
        {
            "query": "How did tariffs impact the supply chain?",
            "ticker": None, 
            "year": None
        }
    ]
    for test in test_queries:
        print(f'\n query: {test["query"]}')
        if test['ticker']:
            print(f' (filter: {test["ticker"]}, {test["year"]})')

        results = search_chunks(query = test['query'], top_k=3, ticker_filter=test['ticker'], year_filter=test['year'])

        print_search_results(results)
if __name__ == '__main__':
    main()                            