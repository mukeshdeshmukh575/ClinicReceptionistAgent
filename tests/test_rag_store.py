import pytest
import json
from sqlalchemy.orm import Session
from app.agent import rag_store
from app.db import models

def test_cosine_similarity():
    # Test identical vectors
    assert rag_store.cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    # Test orthogonal vectors
    assert rag_store.cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    # Test invalid vectors
    assert rag_store.cosine_similarity([1.0], [1.0, 2.0]) == 0.0
    assert rag_store.cosine_similarity([], []) == 0.0

def test_keyword_search_score(db_session: Session):
    doc = models.RagDoc(
        category="Clinic Policy",
        title="Late Cancellation Policy & Rescheduling Fees",
        content="Appointments must be cancelled at least 24 hours prior to avoid late cancellation fee.",
        keywords="cancel, reschedule, policy, fee"
    )
    score_title = rag_store.keyword_search_score("Cancellation", doc)
    score_keyword = rag_store.keyword_search_score("fee", doc)
    score_content = rag_store.keyword_search_score("prior", doc)
    
    assert score_title > score_content
    assert score_keyword > score_content

def test_add_rag_document(db_session: Session):
    doc = rag_store.add_rag_document(
        db_session,
        category="Test Category",
        title="Test Title",
        content="Test content of the document.",
        keywords="test, doc"
    )
    assert doc.id is not None
    assert doc.title == "Test Title"

def test_search_rag_keyword_fallback(db_session: Session):
    # Add a unique test doc
    rag_store.add_rag_document(
        db_session,
        category="Clinic Info",
        title="Test Clinic Hours",
        content="Open Monday to Friday 9 AM to 5 PM.",
        keywords="timings, hours, test"
    )
    # Query matching keywords
    results = rag_store.search_rag(db_session, "test clinic hours", limit=1)
    assert len(results) >= 1
    assert results[0][0].title == "Test Clinic Hours"
    assert results[0][1] > 0.0
