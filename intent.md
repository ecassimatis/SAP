# Apartment Subsidy Eligibility Profile Checker

AI agent that checks a person's profile based on uploaded documents to determine apartment access eligibility and subsidy entitlement, aligned with country-specific legal requirements.

## Business challenge

Housing authorities and real estate administrators need to manually review applicant documents (ID, income proof, residency status, legal compliance records) to assess eligibility for apartment access and government subsidies. This process is slow, error-prone, and inconsistent across agents — causing delays, compliance risk, and poor applicant experience.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Manual review time per application | — | Reduced by ≥ 50% | — | Eligibility and Entitlement Determination | user |
| Application processing turnaround | Multi-day | Same-day | — | Grants and Benefits Application Management | user |

## Key Milestones

1. **Document Ingestion** — Applicant uploads identity, income, and residency documents; agent confirms receipt and completeness.
2. **Document Validation** — Agent extracts and validates key data fields from each document (authenticity, expiry, format compliance).
3. **Legal Compliance Check** — Agent applies country-specific legal rules to verify the applicant meets eligibility criteria for apartment access.
4. **Subsidy Assessment** — Agent evaluates subsidy eligibility based on income thresholds, household size, and applicable benefit programs.
5. **Decision & Report** — Agent produces a structured eligibility report with a recommendation (approve / reject / request more info) and an audit trail.

## Business Architecture (RBA)

### End-to-End Process

Grants and Benefits Delivery (public sector)

### Process Hierarchy

```
Grants and Benefits Delivery (public sector)
└── Grants and Benefits Case Management (public sector)
    └── Manage registration and intake (BPS-361_058)
        └── Application and intake of data
    └── Managing benefits and deductions (BPS-361_059)
        └── Manage benefit decision
        └── Manage deduction decision
    └── Managing grants for the grantor (BPS-361_060)
        └── Manage grants for grantor
```

### Summary

The challenge maps to public-sector Grants and Benefits Delivery, covering intake, eligibility/entitlement determination, and grant assessment — with an additional layer of document validation and legal compliance logic that is not covered by standard SAP products and requires a custom AI agent.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Gap? | Notes / assumptions |
|------------------------|------------------------|------------|-------------------|--------------------|------|---------------------|
| Application intake and data capture | SAP S/4HANA Cloud Private Edition — Grants and Benefits Application Management | — | — | — | No | Covered by S/4HANA public sector module |
| Eligibility and entitlement determination | SAP S/4HANA Cloud Private Edition — Eligibility and Entitlement Determination (SC5051) | — | — | — | No | Mandatory capability available |
| Deduction decision management | SAP S/4HANA Cloud Private Edition — Deduction Decision Management (SC5053) | — | — | — | No | Mandatory capability available |
| Grant assessment and agreement | SAP S/4HANA Cloud Private Edition — Grant Assessment Management (SC5054), Grantor Agreement Management (SC5050) | — | — | — | No | Mandatory capabilities available |
| Document validation (ID, income, residency) | No standard SAP product recommendation | `sap.s4:apiResource:CE_LEGAL_DOCUMENT_0001:v1` | — | — | Yes | Custom AI agent logic required for OCR and validation |
| Legal compliance check (country-specific rules) | No standard SAP product recommendation | — | — | — | Yes | Custom rules engine within the agent, parameterised per country |
| Real estate occupancy / lease context | SAP S/4HANA — Real Estate Occupancy, Real Estate Contracts | `sap.s4:apiResource:CE_REOCCUPANCY_0001:v1`, `sap.s4:apiResource:API_RECONTRACT_0001:v1` | — | — | Maybe | Useful context if integrated with RE-FX module |

### Key findings

- Document validation and country-specific legal compliance checking are not covered by any standard SAP product — these are the primary value drivers for the custom AI agent.
- SAP S/4HANA Cloud Private Edition covers the downstream eligibility, benefit, and grant management processes well; the agent feeds into these processes.
- No MCP servers were found for the relevant APIs; the agent will interact via direct API calls or document parsing tools.
- The solution is a standalone AI agent that processes documents, applies legal rules, and produces a structured eligibility recommendation.
- Real estate APIs (CE_REOCCUPANCY, API_RECONTRACT) can optionally provide housing context if the organization runs SAP RE-FX.

## Recommendations

### AI Agent for Document-Based Subsidy Eligibility Checking

#### Executive Summary

Python AI agent that validates documents and checks subsidy eligibility per country law.

#### Recommended Solution

A pro-code Python AI agent (A2A protocol) that accepts applicant documents (PDF, image), extracts structured data via document intelligence tools, applies country-specific legal eligibility rules, and returns a structured decision report. The agent is built on SAP AI Core, integrates with SAP S/4HANA for downstream grant processing, and exposes a standard A2A endpoint for embedding into housing portals or case management tools.

#### Recommended solution category

AI Agent

#### Intent fit
88%
