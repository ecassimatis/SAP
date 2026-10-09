"""Unit tests for the generate_decision_report tool."""
import pytest
from tools.document_tools import generate_decision_report


def _sample_inputs():
    validated_data = [
        {
            "document_type": "national_id",
            "status": "VALID",
            "extracted_fields": {"name": "Max Mustermann"},
            "validation_errors": [],
        }
    ]
    compliance_result = {
        "country_code": "de",
        "program_code": "social_housing",
        "rules_evaluated": 5,
        "rules_passed": 5,
        "rules_failed": 0,
        "rule_results": [
            {"rule_id": "income_threshold", "result": "PASS", "mandatory": True, "reason": "OK"}
        ],
    }
    assessment = {
        "recommendation": "APPROVE",
        "confidence_score": 100,
        "subsidy_tier": "FULL_SUBSIDY",
        "reasoning": "All rules passed.",
    }
    return validated_data, compliance_result, assessment


def test_report_structure():
    """Report has all required fields."""
    validated_data, compliance_result, assessment = _sample_inputs()
    result = generate_decision_report.invoke({
        "case_id": "CASE-001",
        "applicant_name": "Max Mustermann",
        "validated_data": validated_data,
        "compliance_result": compliance_result,
        "assessment": assessment,
    })
    assert result["case_id"] == "CASE-001"
    assert result["applicant_name"] == "Max Mustermann"
    assert result["recommendation"] == "APPROVE"
    assert result["confidence_score"] == 100
    assert result["subsidy_tier"] == "FULL_SUBSIDY"
    assert "generated_at" in result
    assert "audit_trail" in result
    assert "compliance_summary" in result
    assert "document_summary" in result


def test_report_audit_trail():
    """Audit trail contains agent info and timestamp."""
    validated_data, compliance_result, assessment = _sample_inputs()
    result = generate_decision_report.invoke({
        "case_id": "CASE-002",
        "applicant_name": "Anna Schmidt",
        "validated_data": validated_data,
        "compliance_result": compliance_result,
        "assessment": assessment,
    })
    audit = result["audit_trail"]
    assert audit["agent"] == "apartment-subsidy-eligibility-agent"
    assert audit["case_id"] == "CASE-002"
    assert "timestamp" in audit


def test_report_reject_recommendation():
    """Report correctly reflects REJECT recommendation."""
    validated_data, compliance_result, assessment = _sample_inputs()
    assessment["recommendation"] = "REJECT"
    assessment["subsidy_tier"] = "NONE"
    compliance_result["rules_failed"] = 1

    result = generate_decision_report.invoke({
        "case_id": "CASE-003",
        "applicant_name": "Test User",
        "validated_data": validated_data,
        "compliance_result": compliance_result,
        "assessment": assessment,
    })
    assert result["recommendation"] == "REJECT"
    assert result["subsidy_tier"] == "NONE"
