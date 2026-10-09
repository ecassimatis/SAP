---
name: eligibility-rules
description: Applies country-specific legal eligibility rules to determine housing subsidy entitlement.
---

# Eligibility Rules Skill

## When to Use This Skill

Load this skill when evaluating an applicant's eligibility for a housing subsidy (M3, M4). It requires validated document data and a country/program code.

## Steps

### Step 1: Load Rule Set

Load the rule set from `app/rules/<country_code>.json`. If the file does not exist → emit `M3.missed` with reason "rule set not available" and return an error.

### Step 2: Evaluate Each Rule

For each rule in the rule set, evaluate against the extracted applicant data:

| Rule ID        | Evaluation Logic                                              |
|----------------|---------------------------------------------------------------|
| income_threshold | `net_monthly_income <= rule.max_income`                     |
| residency_duration | `residency_months >= rule.min_months`                    |
| citizenship    | `nationality in rule.allowed_nationalities OR permit_valid == true` |
| household_size | Apply income adjustment factor for households > 1            |
| age_range      | `rule.min_age <= applicant_age <= rule.max_age` (if defined) |
| document_validity | All mandatory documents are VALID (not EXPIRED/UNREADABLE)|

### Step 3: Compute Compliance Result

Return a structured compliance result:
```json
{
  "country_code": "<code>",
  "program_code": "<program>",
  "rules_evaluated": <N>,
  "rules_passed": <M>,
  "rules_failed": <K>,
  "rule_results": [
    {
      "rule_id": "<id>",
      "description": "<human readable>",
      "legal_reference": "<article/law>",
      "result": "PASS | FAIL | UNCLEAR",
      "reason": "<explanation>"
    }
  ]
}
```

### Step 4: Subsidy Tier Determination

Based on passing rules, determine subsidy tier:
- All mandatory rules pass → FULL_SUBSIDY
- Income threshold and residency pass, others unclear → PARTIAL_SUBSIDY
- Income threshold fails → NO_SUBSIDY
- Any FAIL on mandatory rules → REJECT

## Confidence Score

Compute confidence as: `(rules_passed / rules_evaluated) * 100`
- Adjust downward by 10 points for each UNCLEAR result
- Minimum: 0, Maximum: 100

## Error Handling

- Missing rule set file → return error, do not proceed
- Missing applicant data field referenced by a rule → mark rule as UNCLEAR, note the missing field
