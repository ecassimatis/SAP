"""Unit tests for the validate_documents tool."""
import pytest
from tools.document_tools import validate_documents


def _make_docs():
    return [
        {"type": "national_id", "filename": "id.pdf", "content_text": "..."},
        {"type": "payslip", "filename": "pay.pdf", "content_text": "..."},
    ]


def _make_valid_extracted():
    return [
        {
            "document_type": "national_id",
            "status": "VALID",
            "extracted_fields": {
                "name": "Max Mustermann",
                "date_of_birth": "1990-05-15",
                "id_number": "DE12345678",
                "nationality": "DE",
                "expiry": "2030-01-01",
            },
            "validation_errors": [],
        },
        {
            "document_type": "payslip",
            "status": "VALID",
            "extracted_fields": {
                "name": "Max Mustermann",
                "net_income": 1800,
                "currency": "EUR",
                "period": "2024-08",
                "employer": "ACME GmbH",
            },
            "validation_errors": [],
        },
    ]


def test_validate_all_valid():
    """All documents valid → PASSED."""
    result = validate_documents.invoke(
        {"documents": _make_docs(), "extracted_data": _make_valid_extracted()}
    )
    assert result["status"] == "PASSED"
    assert result["validation_errors"] == []


def test_validate_expired_document():
    """One expired document → FAILED."""
    extracted = _make_valid_extracted()
    extracted[0]["status"] = "EXPIRED"
    extracted[0]["validation_errors"] = ["Document expired on 2020-01-01"]

    result = validate_documents.invoke(
        {"documents": _make_docs(), "extracted_data": extracted}
    )
    assert result["status"] == "FAILED"
    assert len(result["validation_errors"]) > 0


def test_validate_incomplete_document():
    """Incomplete document → FAILED."""
    extracted = _make_valid_extracted()
    extracted[1]["status"] = "INCOMPLETE"
    extracted[1]["validation_errors"] = ["Missing: employer"]

    result = validate_documents.invoke(
        {"documents": _make_docs(), "extracted_data": extracted}
    )
    assert result["status"] == "FAILED"


def test_validate_unreadable_document():
    """Unreadable document → FAILED."""
    extracted = _make_valid_extracted()
    extracted[0]["status"] = "UNREADABLE"
    extracted[0]["validation_errors"] = ["Document could not be read"]

    result = validate_documents.invoke(
        {"documents": _make_docs(), "extracted_data": extracted}
    )
    assert result["status"] == "FAILED"
