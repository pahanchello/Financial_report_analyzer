import os
import json
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from qdrant_client.models import PointStruct

from .embeddings import get_embeddings_batch, get_embedding
from .vector_store import get_qdrant_client, create_collection

load_dotenv()

def load_chunks(file_path: Path) -> list:
    with open(file_path, 'r', encoding = 'utf-8') as f:
        return json.load(f)

def index_all_chunks():
    client = get_qdrant_client()
    collection_name = os.getenv('QDRANT_COLLECTION', 'financial_reports')

    create_collection(client, collection_name)

    chunks_dir = Path('data/processed/chunks')
    chunk_files = list(chunks_dir.glob("*_chunks.json"))

    if not chunk_files:
        print('no chunk files found')
        return

    all_points = []
    total_indexed = 0

    print('Starting indexing')
    for file_path in chunk_files:
        print(f'\n Processing {file_path.name}...')
        chunks = load_chunks(file_path)
        batch_size = 32
        for i in tqdm(range(0, len(chunks), batch_size), desc = 'Embedding'):
            batch = chunks[i: i + batch_size]
            texts = [chunk['text'] for chunk in batch]

            try:
                embeddings = get_embeddings_batch(texts)

            except Exception as e:
                print(f'\n Batch failed, falling back to single requests')
                embeddings = [get_embedding(text) for text in texts]

            for j, chunk in enumerate(batch):
                point = PointStruct(
                    id = chunk['chunk_id'],
                    vector = {'dense': embeddings[j]},
                    payload={
                        "text": chunk["text"],
                        "ticker": chunk["metadata"]["ticker"],
                        "fiscal_year": chunk["metadata"]["fiscal_year"],
                        "period_end": chunk["metadata"]["period_end"],
                        "form_type": chunk["metadata"]["form_type"],
                        "item_id": chunk["metadata"]["item_id"],
                        "section_title": chunk["metadata"]["section_title"],
                        "chunk_index": chunk["metadata"]["chunk_index"],
                        "source_filename": chunk["metadata"]["source_filename"]
                    }
                )
                all_points.append(point)   

            if len(all_points) >= 150:
                client.upsert(collection_name=collection_name, points = all_points)
                total_indexed += len(all_points)

    if all_points:
        client.upsert(collection_name=collection_name, points=all_points)

    count = client.count(collection_name=collection_name).count
    print(f'\n Indexing complete! Total points in collection: {count}')

if __name__ == '__main__':
    index_all_chunks()
