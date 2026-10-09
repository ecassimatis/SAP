"""Unit tests for the assess_subsidy_eligibility tool."""
import pytest
from tools.document_tools import assess_subsidy_eligibility


def _passing_compliance():
    return {
        "status": "COMPLETE",
        "country_code": "de",
        "program_code": "social_housing",
        "rules_evaluated": 5,
        "rules_passed": 5,
        "rules_failed": 0,
        "rule_results": [
            {"rule_id": "income_threshold", "result": "PASS", "mandatory": True, "reason": "OK"},
            {"rule_id": "residency_duration", "result": "PASS", "mandatory": True, "reason": "OK"},
            {"rule_id": "citizenship", "result": "PASS", "mandatory": True, "reason": "OK"},
            {"rule_id": "document_validity", "result": "PASS", "mandatory": True, "reason": "OK"},
            {"rule_id": "age_range", "result": "PASS", "mandatory": True, "reason": "OK"},
        ],
    }


def test_assessment_approve_all_pass():
    """All rules pass with high confidence → APPROVE."""
    result = assess_subsidy_eligibility.invoke(
        {"compliance_result": _passing_compliance(), "program_code": "social_housing"}
    )
    assert result["recommendation"] == "APPROVE"
    assert result["confidence_score"] == 100
    assert result["subsidy_tier"] in ("FULL_SUBSIDY", "PARTIAL_SUBSIDY")


def test_assessment_reject_mandatory_fail():
    """Mandatory rule fails → REJECT."""
    compliance = _passing_compliance()
    compliance["rule_results"][0]["result"] = "FAIL"
    compliance["rules_passed"] = 4
    compliance["rules_failed"] = 1

    result = assess_subsidy_eligibility.invoke(
        {"compliance_result": compliance, "program_code": "social_housing"}
    )
    assert result["recommendation"] == "REJECT"
    assert result["subsidy_tier"] == "NONE"


def test_assessment_request_more_info_unclear():
    """Unclear rules lower confidence → REQUEST_MORE_INFO."""
    compliance = _passing_compliance()
    compliance["rule_results"][1]["result"] = "UNCLEAR"
    compliance["rules_passed"] = 4

    result = assess_subsidy_eligibility.invoke(
        {"compliance_result": compliance, "program_code": "social_housing"}
    )
    assert result["recommendation"] == "REQUEST_MORE_INFO"
    assert result["confidence_score"] < 100


def test_assessment_no_rules_evaluated():
    """No rules → low confidence request more info."""
    compliance = {
        "rules_evaluated": 0,
        "rules_passed": 0,
        "rules_failed": 0,
        "rule_results": [],
    }
    result = assess_subsidy_eligibility.invoke(
        {"compliance_result": compliance, "program_code": "social_housing"}
    )
    assert result["recommendation"] == "REQUEST_MORE_INFO"
    assert result["confidence_score"] == 0
