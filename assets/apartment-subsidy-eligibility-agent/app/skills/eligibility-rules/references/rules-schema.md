# Rules Schema Reference

Rule sets are stored as JSON files at `app/rules/<country_code>.json`.

## Schema

```json
{
  "country_code": "de",
  "program_code": "social_housing",
  "program_name": "Social Housing Subsidy",
  "rules": [
    {
      "rule_id": "income_threshold",
      "description": "Net monthly income must not exceed the threshold",
      "legal_reference": "WoGG §13",
      "mandatory": true,
      "type": "income",
      "max_income": 2000,
      "currency": "EUR",
      "household_adjustments": [
        { "members": 2, "additional_allowance": 480 },
        { "members": 3, "additional_allowance": 960 }
      ]
    },
    {
      "rule_id": "residency_duration",
      "description": "Applicant must have resided in the country for at least 6 months",
      "legal_reference": "WoGG §3",
      "mandatory": true,
      "type": "residency",
      "min_months": 6
    },
    {
      "rule_id": "citizenship",
      "description": "Applicant must be a citizen or hold a valid residence permit",
      "legal_reference": "WoGG §3 Abs. 2",
      "mandatory": true,
      "type": "citizenship",
      "allowed_nationalities": ["DE"],
      "permit_accepted": true
    },
    {
      "rule_id": "document_validity",
      "description": "All submitted documents must be valid (not expired or unreadable)",
      "legal_reference": "Internal compliance",
      "mandatory": true,
      "type": "document_check"
    }
  ]
}
```
