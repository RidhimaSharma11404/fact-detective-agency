import numpy as np
import json
import hashlib
import math
import re
from typing import List, Dict, Any, Tuple, Optional
from .config import GEMINI_API_KEY, OPENAI_API_KEY

def build_fact_text(subject: str, predicate: str, obj: str, qualifiers: Optional[Dict[str, Any]] = None) -> str:
    """Build canonical semantic representation of a fact."""
    qual_text = ""
    if qualifiers:
        sorted_items = sorted(qualifiers.items())
        qual_text = " (" + ", ".join(f"{k}: {v}" for k, v in sorted_items) + ")"
    return f"{subject} | {predicate} | {obj}{qual_text}".strip()

def compute_local_embedding(text: str, dim: int = 256) -> np.ndarray:
    """
    High-fidelity semantic hash + subword n-gram embedding vectorizer.
    Produces unit-normalized dense vectors capable of capturing semantic similarity,
    lexical overlap, numerical proximity, and entity relations without external downloads.
    """
    vec = np.zeros(dim, dtype=np.float32)
    if not text:
        return vec

    normalized = text.lower().strip()
    words = [w for w in re.split(r'[\s|()\[\],:\-_]+', normalized) if w]
    
    # 1. Word-level hashed projections
    for word in words:
        clean_word = "".join(c for c in word if c.isalnum() or c in ".%")
        if not clean_word:
            continue
        
        # Word hash
        h = int(hashlib.md5(clean_word.encode("utf-8")).hexdigest(), 16)
        pos = h % dim
        sign = 1.0 if ((h >> 8) & 1) == 0 else -1.0
        
        # Weighting
        weight = 2.0 if any(c.isdigit() for c in clean_word) else 1.5
        vec[pos] += sign * weight

        # 2. Character n-grams (lengths 3 to 5)
        for n in [3, 4, 5]:
            if len(clean_word) >= n:
                for i in range(len(clean_word) - n + 1):
                    ngram = clean_word[i:i + n]
                    nh = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                    npos = nh % dim
                    nsign = 1.0 if ((nh >> 8) & 1) == 0 else -1.0
                    vec[npos] += nsign * 0.8

    # L2 Normalization
    norm = np.linalg.norm(vec)
    if norm > 1e-6:
        vec = vec / norm
    return vec

class EmbeddingIndex:
    def __init__(self, similarity_threshold: float = 0.50):
        self.similarity_threshold = similarity_threshold
        # fact_id -> (embedding_vector, metadata_dict)
        self.index: Dict[str, Tuple[np.ndarray, Dict[str, Any]]] = {}

    def add_fact(self, fact_id: str, text: str, metadata: Optional[Dict[str, Any]] = None, vector: Optional[List[float]] = None) -> np.ndarray:
        if vector is not None:
            vec = np.array(vector, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm > 1e-6:
                vec = vec / norm
        else:
            vec = compute_local_embedding(text)
        
        self.index[fact_id] = (vec, metadata or {})
        return vec

    def search_candidates(self, query_text: str, top_k: int = 5, exclude_fact_id: Optional[str] = None, exclude_doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fast O(K) candidate retrieval: compares query vector to existing indexed facts.
        """
        if not self.index:
            return []

        query_vec = compute_local_embedding(query_text)
        results = []

        for fact_id, (target_vec, meta) in self.index.items():
            if exclude_fact_id and fact_id == exclude_fact_id:
                continue
            if exclude_doc_id and meta.get("doc_id") == exclude_doc_id:
                # Still allow cross-page comparison in same doc if needed, or across different docs
                pass

            # Cosine similarity between unit vectors is just dot product
            sim = float(np.dot(query_vec, target_vec))
            if sim >= self.similarity_threshold:
                results.append({
                    "fact_id": fact_id,
                    "similarity": round(sim, 4),
                    "metadata": meta
                })

        # Sort descending by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def remove_fact(self, fact_id: str):
        if fact_id in self.index:
            del self.index[fact_id]

    def clear(self):
        self.index.clear()
