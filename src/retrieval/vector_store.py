import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

def get_qdrant_client() -> QdrantClient:
    host = os.getenv("QDRANT_HOST", 'localhost')
    port = int(os.getenv('QDRANT_PORT',6333))
    return QdrantClient(host = host, port = port)

def create_collection(client: QdrantClient, collection_name:str):
    collections = client.get_collections().collections
    if any(col.name == collection_name for col in collections):
        print(f'Collection {collection_name} already exists')
        return

    print(f"Creatin collection '{collection_name}'...")
    client.create_collection(
        collection_name = collection_name, 
        vectors_config={
            "dense": VectorParams(size = 768, distance = Distance.COSINE)
        }
    )
    print(f"Collection {collection_name} created successfully")