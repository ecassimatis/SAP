"""Unit tests for the check_legal_compliance tool."""
import pytest
from tools.document_tools import check_legal_compliance


def _valid_data():
    return [
        {
            "document_type": "national_id",
            "status": "VALID",
            "extracted_fields": {
                "name": "Max Mustermann",
                "date_of_birth": "1990-05-15",
                "nationality": "DE",
                "net_income": 1800,
                "residency_months": 12,
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
            },
            "validation_errors": [],
        },
    ]


def test_compliance_all_rules_pass():
    """Valid German applicant — all rules should pass."""
    result = check_legal_compliance.invoke(
        {"validated_data": _valid_data(), "country_code": "de", "program_code": "social_housing"}
    )
    assert result["status"] == "COMPLETE"
    assert result["rules_failed"] == 0
    assert result["rules_passed"] > 0


def test_compliance_income_too_high():
    """Income above threshold → income rule fails."""
    data = _valid_data()
    for d in data:
        d["extracted_fields"]["net_income"] = 5000

    result = check_legal_compliance.invoke(
        {"validated_data": data, "country_code": "de", "program_code": "social_housing"}
    )
    income_rule = next(r for r in result["rule_results"] if r["rule_id"] == "income_threshold")
    assert income_rule["result"] == "FAIL"


def test_compliance_residency_too_short():
    """Residency too short → residency rule fails."""
    data = _valid_data()
    for d in data:
        d["extracted_fields"]["residency_months"] = 2

    result = check_legal_compliance.invoke(
        {"validated_data": data, "country_code": "de", "program_code": "social_housing"}
    )
    residency_rule = next(r for r in result["rule_results"] if r["rule_id"] == "residency_duration")
    assert residency_rule["result"] == "FAIL"


def test_compliance_unknown_country():
    """Unknown country code → ERROR with missing rule set."""
    result = check_legal_compliance.invoke(
        {"validated_data": _valid_data(), "country_code": "xx", "program_code": "housing"}
    )
    assert result["status"] == "ERROR"
    assert "rule set not available" in result.get("error", "").lower()


def test_compliance_expired_documents():
    """Expired document → document_check rule fails."""
    data = _valid_data()
    data[0]["status"] = "EXPIRED"

    result = check_legal_compliance.invoke(
        {"validated_data": data, "country_code": "de", "program_code": "social_housing"}
    )
    doc_rule = next(
        (r for r in result["rule_results"] if r["rule_id"] == "document_validity"), None
    )
    assert doc_rule is not None
    assert doc_rule["result"] == "FAIL"
