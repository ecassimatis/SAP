# Product Requirements Document (PRD)

**Title:** Apartment Subsidy Eligibility Profile Checker Agent
**Date:** 2026-09-21
**Owner:** Housing Authority / Real Estate Administration
**Solution Category:** AI Agent

---

## Product Purpose & Value Proposition

**Elevator Pitch:**
Housing case workers spend days manually reviewing stacks of applicant documents to decide who qualifies for subsidised apartments. This AI agent does it in minutes — extracting data from documents, checking it against country-specific legal rules, and delivering a clear, auditable eligibility recommendation.

**Business Need:**
Eligibility checks for subsidised housing require validating multiple documents (ID, income proof, residency status, family composition) against legal thresholds that vary by country and benefit program. Today this is done manually, causing bottlenecks, inconsistencies, and compliance risk.

**Expected Value:**
- Manual review time reduced by ≥ 50%
- Applications processed on the same day they are submitted
- Consistent, rule-based decisions that reduce the risk of legal challenges

**Product Objectives:**
1. Automate document intake, extraction, and validation to eliminate manual data entry
2. Apply country-specific legal eligibility rules reliably and consistently
3. Produce an auditable decision report that case workers can review and approve

---

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Manual review time per application | — | Reduced by ≥ 50% | — | Eligibility and Entitlement Determination | user |
| Application processing turnaround | Multi-day | Same-day | — | Grants and Benefits Application Management | user |

---

## Requirements

### Must-Have Requirements

**R1: Document Ingestion**
- **User Story:** As a case worker, I need to upload applicant documents (PDF, image) so that the agent can begin the eligibility check automatically.
- **Acceptance Criteria:** Given a case worker submits documents via the intake interface, when the agent receives them, then it confirms receipt, identifies document types, and flags any missing required documents.
- **Priority Rank:** 1

**R2: Document Data Extraction & Validation**
- **User Story:** As a case worker, I need the agent to extract key fields (name, income, dates, identifiers) from documents so that I don't have to manually enter data.
- **Acceptance Criteria:** Given a valid document, when the agent processes it, then structured data is extracted with ≥ 90% accuracy; expired or unreadable documents are flagged.
- **Priority Rank:** 2

**R3: Legal Compliance Check**
- **User Story:** As a compliance officer, I need the agent to apply the correct country-specific legal rules so that eligibility decisions are consistent and defensible.
- **Acceptance Criteria:** Given extracted applicant data, when the agent applies the rule set for the selected country/program, then each rule is evaluated and the result (pass/fail/unclear) is recorded with the rule reference.
- **Priority Rank:** 3

**R4: Subsidy Eligibility Assessment**
- **User Story:** As a case worker, I need the agent to determine whether the applicant qualifies for a subsidy so that I can make a fast, informed decision.
- **Acceptance Criteria:** Given a completed legal check, when the agent computes eligibility, then it produces an overall recommendation (Approve / Reject / Request More Information) with a confidence score.
- **Priority Rank:** 4

**R5: Decision Report & Audit Trail**
- **User Story:** As a compliance officer, I need a structured report with the evidence behind each decision so that we can demonstrate legal compliance in audits.
- **Acceptance Criteria:** Given a completed eligibility assessment, when the report is generated, then it includes applicant data, rule outcomes, recommendation, confidence score, and a timestamp-signed audit trail.
- **Priority Rank:** 5

---

## Solution Architecture

**Architecture Overview:**
A pro-code Python AI agent following the A2A (Agent-to-Agent) protocol, deployed on SAP AI Core. The agent receives document uploads, uses document intelligence tools for extraction, applies a configurable legal rules module, and returns a structured decision report.

**Key Components:**
- **AI Agent (Python / A2A):** Core reasoning and orchestration layer
- **Document Intelligence Tool:** OCR and structured data extraction from PDFs and images
- **Legal Rules Module:** Country-parameterised eligibility rule engine (configurable per program)
- **SAP AI Core:** Hosting and LLM runtime (generative AI for document understanding)
- **Audit Log Store:** Persistent, tamper-evident log of all decisions and evidence

**Integration Points:**
- SAP S/4HANA Legal Document API (`CE_LEGAL_DOCUMENT_0001`) — legal document reference data
- SAP S/4HANA Real Estate Occupancy API (`CE_REOCCUPANCY_0001`) — optional housing context
- Housing portal or case management system — entry point for document submissions

---

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The agent is designed with a pluggable rules module so that new countries or benefit programs can be added without modifying core agent logic.
- Document type handlers (e.g., payslip, national ID, tenancy contract) are independently extensible.
- New tools (e.g., credit check, criminal record query) can be registered without changes to the orchestration layer.

**Business Step Instrumentation:**
All key business steps emit structured log statements for observability and monitoring on SAP AI Core. Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`

---

### Automation & Agent Behaviour

**Automation Level:** ML-assisted with human-in-the-loop approval for final decisions

**Actions performed without human approval:**
- Document ingestion and type classification
- Data extraction from documents
- Rule evaluation against legal thresholds
- Generation of eligibility recommendation

**Actions requiring human review or approval:**
- Final approval or rejection of an application (case worker confirms)
- Cases where the agent confidence score is below threshold (routed to human)
- Cases with missing or unreadable documents

**Model used:** LLM via SAP Generative AI Hub (GPT-4o or equivalent) for document understanding; deterministic rule engine for legal compliance evaluation

**Knowledge & data sources accessed:**
- Uploaded applicant documents (PDF, image)
- Country-specific legal rule sets (configurable JSON/YAML)
- SAP S/4HANA Legal Document reference data (read-only)

**Tools or connectors invoked:**
- Document extraction tool: OCR and field extraction (read-only)
- Legal rules engine: rule evaluation against extracted data (read-only)
- SAP Legal Document API: legal reference data lookup (read-only)
- Audit log writer: records decision evidence (write)

**Guardrails & fail-safes:**
- Agent never writes to core ERP systems autonomously — only produces recommendations
- Confidence below 70% automatically routes the case to a human case worker
- Missing mandatory documents block the eligibility check and notify the applicant
- All rule evaluations cite the legal article or threshold applied

---

## Milestones

### M1: Document Ingestion
- **Description:** Applicant documents are received and classified by the agent.
- **Achieved when:** All submitted documents are received, type-classified, and completeness is confirmed.
- **Log on achievement:** `M1.achieved: document ingestion complete — <N> documents received, types: <list>`
- **Log on miss:** `M1.missed: document ingestion failed or incomplete — missing: <list>`

### M2: Document Validation
- **Description:** Key data fields are extracted and validated from each document.
- **Achieved when:** Structured data is extracted from all documents with no critical extraction errors.
- **Log on achievement:** `M2.achieved: document validation complete — all fields extracted successfully`
- **Log on miss:** `M2.missed: document validation failed — unreadable or expired documents: <list>`

### M3: Legal Compliance Check
- **Description:** Country-specific legal rules are evaluated against extracted applicant data.
- **Achieved when:** All applicable rules for the selected country/program have been evaluated.
- **Log on achievement:** `M3.achieved: legal compliance check complete — <N> rules passed, <M> failed`
- **Log on miss:** `M3.missed: legal compliance check incomplete — rule set not available for country: <country>`

### M4: Subsidy Assessment
- **Description:** Subsidy eligibility is computed based on the compliance check result.
- **Achieved when:** An eligibility recommendation with confidence score has been produced.
- **Log on achievement:** `M4.achieved: subsidy assessment complete — recommendation: <Approve|Reject|More Info>, confidence: <score>`
- **Log on miss:** `M4.missed: subsidy assessment could not be completed — reason: <reason>`

### M5: Decision Report Generated
- **Description:** A structured, auditable decision report is produced and stored.
- **Achieved when:** The report is generated, signed with a timestamp, and available for case worker review.
- **Log on achievement:** `M5.achieved: decision report generated — case ID: <id>, recommendation: <result>`
- **Log on miss:** `M5.missed: decision report generation failed — case ID: <id>`
