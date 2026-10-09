---
name: document-validation
description: Validates applicant documents by classifying type, extracting mandatory fields, and flagging issues.
---

# Document Validation Skill

## When to Use This Skill

Load this skill when processing applicant documents for housing subsidy eligibility. Use it during the document validation phase (M2) to extract structured data.

## Document Types and Required Fields

### National Identity Card / Passport
- Full name
- Date of birth
- ID/passport number
- Nationality
- Expiry date
- Issuing country

### Proof of Income (Payslip or Bank Statement)
- Full name (must match ID)
- Net monthly income amount
- Currency
- Period/month of statement
- Employer name (payslip only) or bank name (bank statement)

### Proof of Residency
- Full name (must match ID)
- Current address
- Date of issue or validity period
- Issuing authority (municipality, utility company, etc.)

### Tenancy Contract (optional)
- Landlord name
- Tenant name (must match ID)
- Property address
- Contract start and end dates
- Monthly rent amount

## Validation Rules

1. **Expiry check**: Any document with an expiry date in the past must be flagged as EXPIRED.
2. **Name consistency**: The full name on the ID/passport must match the name on all other documents (allowing for minor formatting differences, e.g., first/last name order).
3. **Completeness**: All mandatory fields for the document type must be present. Missing fields → flag as INCOMPLETE.
4. **Readability**: If a document is unreadable (corrupted, blurred, blank) → flag as UNREADABLE.
5. **Date format**: All dates must be parsed and normalized to ISO 8601 (YYYY-MM-DD). If a date cannot be parsed → flag the field as INVALID_DATE.

## Output Format

Return a structured JSON object per document:
```json
{
  "document_type": "<type>",
  "status": "VALID | EXPIRED | INCOMPLETE | UNREADABLE | INVALID_DATE",
  "extracted_fields": { "<field>": "<value>" },
  "validation_errors": ["<error description>"]
}
```

## Error Handling

- If a document cannot be classified → set `document_type` to `UNKNOWN` and `status` to `UNREADABLE`.
- Do NOT guess field values. If a field cannot be read, mark it as `null` and add it to `validation_errors`.
