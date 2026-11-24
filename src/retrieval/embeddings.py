import os
import requests
from typing import List

def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    host = os.getenve("OLLAMA_HOST", 'http://localhost:11434')
    model = os.getenv("EMBEDDING_MODEL", 'nomic-embed-text')

    response = requests.post(
        f'{host}/api/embed',
        json={
            'model':model,
            'input':texts
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json()['embeddings']

def get_embedding(text:str) -> List[float]:
    host = os.getenv("OLLAMA_HOST", 'http://localhost:11434')
    model = os.getenv('EMBEDDING_MODEL','nomic-embed-text')
    response = requests.post(
        f'{host}/api/embeddings',
        json = {
                'model':model,
                'prompt': text
        },
        timeout = 60
    )
    response.raise_for_status()
    return response.json()['embedding']