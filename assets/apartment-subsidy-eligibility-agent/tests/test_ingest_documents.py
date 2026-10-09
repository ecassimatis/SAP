"""Unit tests for the ingest_documents tool."""
import pytest
from tools.document_tools import ingest_documents


def test_ingest_complete_documents():
    """Test ingestion with all required document types present."""
    docs = [
        {"type": "national_id", "filename": "id.pdf", "content_text": "..."},
        {"type": "payslip", "filename": "pay.pdf", "content_text": "..."},
        {"type": "residency_proof", "filename": "res.pdf", "content_text": "..."},
    ]
    result = ingest_documents.invoke({"documents": docs})
    assert result["status"] == "COMPLETE"
    assert result["document_count"] == 3
    assert result["missing_required"] == []


def test_ingest_incomplete_documents_missing_income():
    """Test ingestion with missing income document."""
    docs = [
        {"type": "national_id", "filename": "id.pdf", "content_text": "..."},
        {"type": "residency_proof", "filename": "res.pdf", "content_text": "..."},
    ]
    result = ingest_documents.invoke({"documents": docs})
    assert result["status"] == "INCOMPLETE"
    assert len(result["missing_required"]) > 0
    assert any("income" in m for m in result["missing_required"])


def test_ingest_incomplete_documents_missing_id():
    """Test ingestion with missing identity document."""
    docs = [
        {"type": "payslip", "filename": "pay.pdf", "content_text": "..."},
        {"type": "residency_proof", "filename": "res.pdf", "content_text": "..."},
    ]
    result = ingest_documents.invoke({"documents": docs})
    assert result["status"] == "INCOMPLETE"
    assert any("identity" in m for m in result["missing_required"])


def test_ingest_accepts_passport_as_id():
    """Test that passport is accepted as identity document."""
    docs = [
        {"type": "passport", "filename": "passport.pdf", "content_text": "..."},
        {"type": "bank_statement", "filename": "bank.pdf", "content_text": "..."},
        {"type": "residency_proof", "filename": "res.pdf", "content_text": "..."},
    ]
    result = ingest_documents.invoke({"documents": docs})
    assert result["status"] == "COMPLETE"


def test_ingest_empty_documents():
    """Test ingestion with empty document list."""
    result = ingest_documents.invoke({"documents": []})
    assert result["status"] == "INCOMPLETE"
    assert len(result["missing_required"]) > 0
