"""
Simple RAG engine for documentation queries
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import markdown
from sentence_transformers import SentenceTransformer
import numpy as np

DOCS_DIR = Path("../docs")


class RAGEngine:
    def __init__(self):
        self.model = None  # Lazy initialization
        self.docs = []
        self.embeddings = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of model and docs"""
        if self._initialized:
            return
        
        print("Initializing RAG engine (this may take a moment on first use)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._load_docs()
        self._initialized = True
    
    def _load_docs(self):
        """Load and index markdown documentation"""
        if not DOCS_DIR.exists():
            print(f"Warning: Docs directory {DOCS_DIR} not found")
            return
        
        for md_file in DOCS_DIR.glob("*.md"):
            with open(md_file, 'r') as f:
                content = f.read()
                # Simple chunking by paragraphs
                chunks = content.split('\n\n')
                for chunk in chunks:
                    if len(chunk.strip()) > 50:  # Skip very short chunks
                        self.docs.append({
                            "text": chunk.strip(),
                            "source": md_file.name
                        })
        
        if self.docs and self.model:
            texts = [doc["text"] for doc in self.docs]
            self.embeddings = self.model.encode(texts)
            print(f"Loaded {len(self.docs)} document chunks")
    
    def query(self, query: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
        """Query RAG engine"""
        # Initialize only when needed (lazy loading)
        self._ensure_initialized()
        
        if not self.docs or self.embeddings is None:
            return None
        
        query_embedding = self.model.encode([query])
        
        # Cosine similarity
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        if similarities[top_indices[0]] < 0.3:  # Low similarity threshold
            return None
        
        results = []
        for idx in top_indices:
            results.append({
                "text": self.docs[idx]["text"],
                "source": self.docs[idx]["source"],
                "score": float(similarities[idx])
            })
        
        # Combine results into answer
        answer = "\n\n".join([f"From {r['source']}:\n{r['text']}" for r in results])
        
        return {
            "answer": answer,
            "sources": [r["source"] for r in results],
            "score": float(similarities[top_indices[0]])
        }

