import os
from dotenv import load_dotenv
import requests
from qdrant_client import QdrantClient

load_dotenv()

def test_ollama():
    """Проверяет Ollama"""
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    print(f"\n Testing Ollama at {host}...")
    
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        print(f" Ollama is running!")
        print(f" Available models: {len(models)}")
        for model in models:
            print(f"   - {model['name']}")
        
        model_names = [m['name'] for m in models]
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        llm_model = os.getenv("LLM_MODEL", "qwen2.5:7b-instruct-q4_K_M")
        
        embedding_found = any(name.startswith(embedding_model) for name in model_names)
        llm_found = any(name.startswith(llm_model) for name in model_names)
        
        if not embedding_found:
            print(f"  Warning: {embedding_model} not found!")
        else:
            print(f"Embedding model found: {embedding_model}")
        
        if not llm_found:
            print(f"Warning: {llm_model} not found!")
        else:
            print(f"LLM model found: {llm_model}")
        
        return True
        
    except Exception as e:
        print(f"Ollama error: {e}")
        return False


def test_qdrant():
    """Проверяет Qdrant"""
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", 6333))
    print(f"\nTesting Qdrant at {host}:{port}...")
    
    try:
        client = QdrantClient(host=host, port=port)
        
        collections = client.get_collections()
        print(f"Qdrant is running!")
        print(f" Collections: {len(collections.collections)}")
        for col in collections.collections:
            print(f"   - {col.name}")
        
        return True
        
    except Exception as e:
        print(f"Qdrant error: {e}")
        return False


def test_embedding():
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    
    print(f"\nTesting embedding model '{model}'...")
    
    try:
        response = requests.post(
            f"{host}/api/embeddings",
            json={
                "model": model,
                "prompt": "Apple's revenue in 2026 was $478 billion."
            },
            timeout=30
        )
        response.raise_for_status()
        
        embedding = response.json()["embedding"]
        print(f"Embedding generated!")
        print(f"Dimensions: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
        
        if len(embedding) != 768:
            print(f" Warning: expected 768 dimensions, got {len(embedding)}")
        else:
            print(f" Correct dimensions (768)")
        
        return True
        
    except Exception as e:
        print(f"Embedding error: {e}")
        return False


def main():
    print("=" * 60)
    print(" Connection Test")
    print("=" * 60)
    
    ollama_ok = test_ollama()
    qdrant_ok = test_qdrant()
    embedding_ok = test_embedding() if ollama_ok else False
    
    results = {
        "Ollama": ollama_ok,
        "Qdrant": qdrant_ok,
        "Embedding": embedding_ok
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"{name:15} {status}")
    
    if all(results.values()):
        print("\nAll systems ready! Let's vectorize!")
    else:
        print("\nSome checks failed. Fix issues before proceeding.")


if __name__ == "__main__":
    main()