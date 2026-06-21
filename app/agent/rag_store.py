import os
import sys
import json
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Ensure parent directory of 'app' is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Load environment variables
load_dotenv()

import google.generativeai as genai
from app.db import models

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def get_embedding(text: str) -> list[float]:
    """Generates embeddings using Gemini API if configured."""
    if not api_key:
        return []
    try:
        response = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return response["embedding"]
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

def cosine_similarity(v1, v2):
    """Computes cosine similarity between two vectors in plain Python."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = sum(x * x for x in v1) ** 0.5
    norm_v2 = sum(x * x for x in v2) ** 0.5
    if not norm_v1 or not norm_v2:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def keyword_search_score(query: str, doc: models.RagDoc) -> float:
    """Calculates a simple matching score based on overlapping keywords and terms."""
    query_tokens = set(query.lower().split())
    # Remove common short words
    stopwords = {"the", "a", "an", "and", "or", "but", "is", "are", "of", "to", "for", "in", "at", "on", "with"}
    query_tokens = query_tokens - stopwords
    
    if not query_tokens:
        return 0.0
        
    score = 0.0
    content_lower = doc.content.lower()
    title_lower = doc.title.lower()
    keywords_lower = (doc.keywords or "").lower()
    
    for token in query_tokens:
        if token in title_lower:
            score += 2.0  # Higher weight for titles
        if token in keywords_lower:
            score += 1.5  # Medium weight for keywords
        if token in content_lower:
            score += 0.5  # Lower weight for general content
            
    return score

def add_rag_document(db: Session, category: str, title: str, content: str, keywords: str = None) -> models.RagDoc:
    """Adds a document to the RAG store and computes its embedding if possible."""
    # Compute embedding for storage
    embedding_vector = []
    if api_key:
        try:
            response = genai.embed_content(
                model="models/text-embedding-004",
                content=content,
                task_type="retrieval_document"
            )
            embedding_vector = response["embedding"]
        except Exception as e:
            print(f"Error seeding embedding: {e}")
            
    db_doc = models.RagDoc(
        category=category,
        title=title,
        content=content,
        keywords=keywords,
        embedding=json.dumps(embedding_vector) if embedding_vector else None
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

def search_rag(db: Session, query: str, limit: int = 3) -> list[tuple[models.RagDoc, float]]:
    """
    Searches the RAG database using vector similarity if embeddings are active, 
    otherwise falls back to keyword matching.
    Returns list of (RagDoc, score) sorted by similarity/relevance.
    """
    docs = db.query(models.RagDoc).all()
    if not docs:
        return []
        
    query_vector = get_embedding(query)
    results = []
    
    if query_vector:
        # Use Semantic Vector Search
        for doc in docs:
            doc_vector = []
            if doc.embedding:
                try:
                    doc_vector = json.loads(doc.embedding)
                except Exception:
                    pass
            
            similarity = 0.0
            if doc_vector:
                similarity = cosine_similarity(query_vector, doc_vector)
            else:
                # Fallback to keyword if this specific doc lacks embedding
                similarity = keyword_search_score(query, doc) * 0.1  # Normalize score scale
                
            results.append((doc, similarity))
        
        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
    else:
        # Use Keyword Search fallback
        for doc in docs:
            score = keyword_search_score(query, doc)
            if score > 0:
                results.append((doc, score))
        results.sort(key=lambda x: x[1], reverse=True)
        
    return results[:limit]
