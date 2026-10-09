"""
Document ingestion, validation, and report generation tools for the
Apartment Subsidy Eligibility Agent.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

REQUIRED_DOCUMENT_TYPES = {"national_id", "passport", "payslip", "bank_statement", "residency_proof"}
MANDATORY_ANY_ID = {"national_id", "passport"}
MANDATORY_ANY_INCOME = {"payslip", "bank_statement"}
MANDATORY_RESIDENCY = {"residency_proof"}


@tool
def ingest_documents(documents: list[dict]) -> dict:
    """
    Ingest and classify applicant documents for eligibility checking.

    Args:
        documents: List of document objects, each with keys:
                   - type (str): Document type hint (e.g. 'national_id', 'payslip')
                   - filename (str): Original filename
                   - content_text (str): Extracted text content of the document

    Returns:
        dict with keys: document_count, classified_types, missing_required, status
    """
    received_types = [doc.get("type", "unknown") for doc in documents]
    has_id = bool(MANDATORY_ANY_ID.intersection(set(received_types)))
    has_income = bool(MANDATORY_ANY_INCOME.intersection(set(received_types)))
    has_residency = bool(MANDATORY_RESIDENCY.intersection(set(received_types)))

    missing = []
    if not has_id:
        missing.append("identity document (national_id or passport)")
    if not has_income:
        missing.append("proof of income (payslip or bank_statement)")
    if not has_residency:
        missing.append("proof of residency")

    if missing:
        logger.info("[M1.missed]: document ingestion failed or incomplete — missing: %s", missing)
        return {
            "status": "INCOMPLETE",
            "document_count": len(documents),
            "classified_types": received_types,
            "missing_required": missing,
        }

    logger.info(
        "[M1.achieved]: document ingestion complete — %d documents received, types: %s",
        len(documents),
        received_types,
    )
    return {
        "status": "COMPLETE",
        "document_count": len(documents),
        "classified_types": received_types,
        "missing_required": [],
    }


@tool
def validate_documents(documents: list[dict], extracted_data: list[dict]) -> dict:
    """
    Validate extracted data from applicant documents.

    Args:
        documents: Original list of document objects (type, filename, content_text).
        extracted_data: List of extracted data objects per document, each with keys:
                        - document_type (str)
                        - extracted_fields (dict)
                        - validation_errors (list[str])
                        - status (str): VALID, EXPIRED, INCOMPLETE, UNREADABLE, INVALID_DATE

    Returns:
        dict with keys: status, validated_data, validation_errors
    """
    all_errors = []
    for item in extracted_data:
        doc_type = item.get("document_type", "unknown")
        status = item.get("status", "UNKNOWN")
        errors = item.get("validation_errors", [])
        if status != "VALID":
            all_errors.append(f"{doc_type}: {status} — {'; '.join(errors) if errors else 'no details'}")

    if all_errors:
        logger.info(
            "[M2.missed]: document validation failed — unreadable or expired documents: %s",
            all_errors,
        )
        return {
            "status": "FAILED",
            "validated_data": extracted_data,
            "validation_errors": all_errors,
        }

    logger.info("[M2.achieved]: document validation complete — all fields extracted successfully")
    return {
        "status": "PASSED",
        "validated_data": extracted_data,
        "validation_errors": [],
    }


@tool
def check_legal_compliance(validated_data: list[dict], country_code: str, program_code: str) -> dict:
    """
    Apply country-specific legal eligibility rules to validated applicant data.

    Args:
        validated_data: List of validated document data objects from validate_documents.
        country_code: ISO country code (e.g. 'de', 'fr').
        program_code: Benefit program identifier (e.g. 'social_housing').

    Returns:
        dict with keys: country_code, program_code, rules_evaluated, rules_passed,
                        rules_failed, rule_results, status
    """
    rules_path = os.path.join(os.path.dirname(__file__), "..", "rules", f"{country_code}.json")

    if not os.path.exists(rules_path):
        logger.info(
            "[M3.missed]: legal compliance check incomplete — rule set not available for country: %s",
            country_code,
        )
        return {
            "status": "ERROR",
            "error": f"Rule set not available for country: {country_code}",
            "rules_evaluated": 0,
            "rules_passed": 0,
            "rules_failed": 0,
            "rule_results": [],
        }

    with open(rules_path) as f:
        rule_set = json.load(f)

    # Build a flat lookup of applicant data from validated documents
    applicant_data: dict[str, Any] = {}
    doc_statuses = []
    for doc in validated_data:
        fields = doc.get("extracted_fields", {})
        applicant_data.update(fields)
        doc_statuses.append(doc.get("status", "UNKNOWN"))

    rules = rule_set.get("rules", [])
    rule_results = []
    passed = 0
    failed = 0

    for rule in rules:
        rule_id = rule.get("rule_id")
        rule_type = rule.get("type")
        result = "PASS"
        reason = "Rule satisfied."

        if rule_type == "income":
            income = applicant_data.get("net_income") or applicant_data.get("net_monthly_income")
            max_income = rule.get("max_income", float("inf"))
            if income is None:
                result = "UNCLEAR"
                reason = "Net monthly income not found in documents."
            else:
                try:
                    if float(income) > max_income:
                        result = "FAIL"
                        reason = f"Income {income} exceeds threshold {max_income} {rule.get('currency', '')}."
                    else:
                        reason = f"Income {income} is within threshold {max_income} {rule.get('currency', '')}."
                except (ValueError, TypeError):
                    result = "UNCLEAR"
                    reason = f"Could not parse income value: {income}"

        elif rule_type == "residency":
            residency_months = applicant_data.get("residency_months")
            min_months = rule.get("min_months", 0)
            if residency_months is None:
                result = "UNCLEAR"
                reason = "Residency duration not found in documents."
            else:
                try:
                    if int(residency_months) < min_months:
                        result = "FAIL"
                        reason = f"Residency {residency_months} months is below minimum {min_months} months."
                    else:
                        reason = f"Residency {residency_months} months meets requirement."
                except (ValueError, TypeError):
                    result = "UNCLEAR"
                    reason = "Could not parse residency duration."

        elif rule_type == "citizenship":
            nationality = applicant_data.get("nationality", "")
            permit_valid = applicant_data.get("permit_valid", False)
            allowed = rule.get("allowed_nationalities", [])
            permit_accepted = rule.get("permit_accepted", False)
            if nationality in allowed or (permit_accepted and permit_valid):
                reason = "Citizenship/permit requirement satisfied."
            else:
                result = "FAIL"
                reason = f"Nationality '{nationality}' not in allowed list and no valid permit found."

        elif rule_type == "document_check":
            bad_docs = [s for s in doc_statuses if s not in ("VALID",)]
            if bad_docs:
                result = "FAIL"
                reason = f"Some documents are not valid: {bad_docs}"
            else:
                reason = "All documents are valid."

        elif rule_type == "age":
            dob_str = applicant_data.get("date_of_birth") or applicant_data.get("dob")
            min_age = rule.get("min_age", 0)
            if dob_str is None:
                result = "UNCLEAR"
                reason = "Date of birth not found."
            else:
                try:
                    dob = datetime.fromisoformat(str(dob_str))
                    today = datetime.now(tz=timezone.utc)
                    age = (today.year - dob.year) - (
                        (today.month, today.day) < (dob.month, dob.day)
                    )
                    if age < min_age:
                        result = "FAIL"
                        reason = f"Applicant age {age} is below minimum {min_age}."
                    else:
                        reason = f"Applicant age {age} meets minimum age requirement."
                except Exception:
                    result = "UNCLEAR"
                    reason = f"Could not parse date of birth: {dob_str}"

        if result == "PASS":
            passed += 1
        elif result == "FAIL":
            failed += 1

        rule_results.append({
            "rule_id": rule_id,
            "description": rule.get("description", ""),
            "legal_reference": rule.get("legal_reference", ""),
            "mandatory": rule.get("mandatory", False),
            "result": result,
            "reason": reason,
        })

    logger.info(
        "[M3.achieved]: legal compliance check complete — %d rules passed, %d failed",
        passed,
        failed,
    )
    return {
        "status": "COMPLETE",
        "country_code": country_code,
        "program_code": program_code,
        "rules_evaluated": len(rules),
        "rules_passed": passed,
        "rules_failed": failed,
        "rule_results": rule_results,
    }


@tool
def assess_subsidy_eligibility(compliance_result: dict, program_code: str) -> dict:
    """
    Compute overall subsidy eligibility recommendation and confidence score.

    Args:
        compliance_result: Output from check_legal_compliance.
        program_code: Benefit program identifier.

    Returns:
        dict with keys: recommendation, confidence_score, subsidy_tier, reasoning
    """
    try:
        rules_evaluated = compliance_result.get("rules_evaluated", 0)
        rules_passed = compliance_result.get("rules_passed", 0)
        rules_failed = compliance_result.get("rules_failed", 0)
        rule_results = compliance_result.get("rule_results", [])

        if rules_evaluated == 0:
            logger.info(
                "[M4.missed]: subsidy assessment could not be completed — reason: no rules evaluated"
            )
            return {
                "recommendation": "REQUEST_MORE_INFO",
                "confidence_score": 0,
                "subsidy_tier": "NONE",
                "reasoning": "No rules were evaluated. Insufficient data.",
            }

        unclear_count = sum(1 for r in rule_results if r.get("result") == "UNCLEAR")
        mandatory_failed = [
            r for r in rule_results if r.get("result") == "FAIL" and r.get("mandatory")
        ]

        # Confidence: base on pass rate, deduct 10 per unclear
        base_confidence = (rules_passed / rules_evaluated) * 100
        confidence_score = max(0, int(base_confidence - (unclear_count * 10)))

        if mandatory_failed:
            recommendation = "REJECT"
            subsidy_tier = "NONE"
            reasoning = f"Mandatory rules failed: {[r['rule_id'] for r in mandatory_failed]}"
        elif unclear_count > 0 or confidence_score < 70:
            recommendation = "REQUEST_MORE_INFO"
            subsidy_tier = "PARTIAL"
            reasoning = f"Confidence score {confidence_score}% below threshold. Unclear rules: {unclear_count}."
        else:
            recommendation = "APPROVE"
            subsidy_tier = "FULL_SUBSIDY" if confidence_score >= 90 else "PARTIAL_SUBSIDY"
            reasoning = f"All mandatory rules passed with confidence score {confidence_score}%."

        logger.info(
            "[M4.achieved]: subsidy assessment complete — recommendation: %s, confidence: %d",
            recommendation,
            confidence_score,
        )
        return {
            "recommendation": recommendation,
            "confidence_score": confidence_score,
            "subsidy_tier": subsidy_tier,
            "reasoning": reasoning,
        }

    except Exception as e:
        logger.info(
            "[M4.missed]: subsidy assessment could not be completed — reason: %s", str(e)
        )
        return {
            "recommendation": "REQUEST_MORE_INFO",
            "confidence_score": 0,
            "subsidy_tier": "NONE",
            "reasoning": f"Assessment failed: {str(e)}",
        }


@tool
def generate_decision_report(
    case_id: str,
    applicant_name: str,
    validated_data: list[dict],
    compliance_result: dict,
    assessment: dict,
) -> dict:
    """
    Generate a structured, auditable decision report for the eligibility case.

    Args:
        case_id: Unique identifier for this application case.
        applicant_name: Full name of the applicant.
        validated_data: Output from validate_documents.
        compliance_result: Output from check_legal_compliance.
        assessment: Output from assess_subsidy_eligibility.

    Returns:
        dict: Structured decision report with timestamp and audit trail.
    """
    try:
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        document_summary = [
            {
                "type": d.get("document_type", "unknown"),
                "status": d.get("status", "UNKNOWN"),
                "errors": d.get("validation_errors", []),
            }
            for d in validated_data
        ]

        report = {
            "case_id": case_id,
            "applicant_name": applicant_name,
            "generated_at": timestamp,
            "country_code": compliance_result.get("country_code", ""),
            "program_code": compliance_result.get("program_code", ""),
            "document_summary": document_summary,
            "compliance_summary": {
                "rules_evaluated": compliance_result.get("rules_evaluated", 0),
                "rules_passed": compliance_result.get("rules_passed", 0),
                "rules_failed": compliance_result.get("rules_failed", 0),
                "rule_results": compliance_result.get("rule_results", []),
            },
            "recommendation": assessment.get("recommendation", "REQUEST_MORE_INFO"),
            "confidence_score": assessment.get("confidence_score", 0),
            "subsidy_tier": assessment.get("subsidy_tier", "NONE"),
            "reasoning": assessment.get("reasoning", ""),
            "audit_trail": {
                "agent": "apartment-subsidy-eligibility-agent",
                "version": "1.0.0",
                "timestamp": timestamp,
                "case_id": case_id,
            },
        }

        logger.info(
            "[M5.achieved]: decision report generated — case ID: %s, recommendation: %s",
            case_id,
            assessment.get("recommendation"),
        )
        return report

    except Exception as e:
        logger.info(
            "[M5.missed]: decision report generation failed — case ID: %s", case_id
        )
        return {
            "case_id": case_id,
            "status": "ERROR",
            "error": str(e),
        }
