# Specification: apartment-subsidy-eligibility-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read the project input (`product-requirements-document.md`, `intent.md`)
- [x] Bootstrap agent code in `assets/apartment-subsidy-eligibility-agent/` using instructions from the `sap-agent-bootstrap` section (invoke from inside `assets/apartment-subsidy-eligibility-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

The agent requires two runtime skills due to complex multi-step domain logic:

- [x] Create `assets/apartment-subsidy-eligibility-agent/app/skills/document-validation/SKILL.md` with step-by-step instructions for:
  - Identifying document type (national ID, passport, payslip, tenancy contract, residence permit, bank statement)
  - Extracting mandatory fields per document type (name, DOB, ID number, income amount, currency, valid dates, issuing authority)
  - Flagging expired, incomplete, or unreadable documents
  - Companion file: `references/document-types.md` listing required fields per type

- [x] Create `assets/apartment-subsidy-eligibility-agent/app/skills/eligibility-rules/SKILL.md` with step-by-step instructions for:
  - Loading the country-specific rule set from `assets/rules/<country-code>.json`
  - Evaluating income threshold, household size, residency duration, and citizenship criteria
  - Computing subsidy tier (full / partial / none)
  - Producing a structured result with per-rule pass/fail and legal article references
  - Companion file: `references/rules-schema.md` documenting the JSON rule schema
  - Example file: `examples/sample-rules-de.json` with a Germany example rule set

---

## Project-Specific Tasks

### Document Ingestion Tool (M1)

- [x] Implement tool `ingest_documents(documents: list[dict]) -> dict` that:
  - Accepts a list of document objects (each with `type`, `filename`, `content_base64`)
  - Validates that mandatory document types are present: national ID (or passport), proof of income (payslip or bank statement), proof of residency
  - Returns a structured receipt with document count, classified types, and a list of missing required documents
  - Emits `M1.achieved: document ingestion complete — <N> documents received, types: <list>` on success
  - Emits `M1.missed: document ingestion failed or incomplete — missing: <list>` when required documents are absent

### Document Validation Tool (M2)

- [x] Implement tool `validate_documents(ingested_documents: dict) -> dict` that:
  - Invokes the `document-validation` runtime skill via `load("skills/document-validation/SKILL.md")`
  - Extracts structured data fields from each document using the LLM (content is passed as text/base64)
  - Validates expiry dates and cross-checks name consistency across documents
  - Returns a `validated_data` object with extracted fields per document and a `validation_errors` list
  - Emits `M2.achieved: document validation complete — all fields extracted successfully` on success
  - Emits `M2.missed: document validation failed — unreadable or expired documents: <list>` on failure

### Legal Compliance Check Tool (M3)

- [x] Implement tool `check_legal_compliance(validated_data: dict, country_code: str, program_code: str) -> dict` that:
  - Invokes the `eligibility-rules` runtime skill via `load("skills/eligibility-rules/SKILL.md")`
  - Loads rule set from `app/rules/<country_code>.json`
  - Evaluates each rule against the validated applicant data
  - Returns a `compliance_result` object with per-rule outcomes (pass/fail/unclear) and legal article references
  - Emits `M3.achieved: legal compliance check complete — <N> rules passed, <M> failed` on success
  - Emits `M3.missed: legal compliance check incomplete — rule set not available for country: <country>` when rule set is missing

- [x] Create `assets/apartment-subsidy-eligibility-agent/app/rules/` directory with a sample rule file `de.json` for Germany covering:
  - Net monthly income threshold (e.g., ≤ €2,000 for single applicant)
  - Minimum residency duration (e.g., ≥ 6 months)
  - Citizenship / residence permit validity
  - Household size adjustments

### Subsidy Assessment Tool (M4)

- [x] Implement tool `assess_subsidy_eligibility(compliance_result: dict, program_code: str) -> dict` that:
  - Computes overall eligibility: Approve / Reject / Request More Information
  - Calculates a confidence score (0–100) based on the fraction of rules passed and data completeness
  - Maps passing rules to subsidy tier (full / partial / none)
  - Returns an `assessment` object with recommendation, confidence score, and subsidy tier
  - Emits `M4.achieved: subsidy assessment complete — recommendation: <result>, confidence: <score>` on success
  - Emits `M4.missed: subsidy assessment could not be completed — reason: <reason>` on failure

### Decision Report Tool (M5)

- [x] Implement tool `generate_decision_report(case_id: str, applicant_name: str, validated_data: dict, compliance_result: dict, assessment: dict) -> dict` that:
  - Assembles a structured JSON report containing: case ID, applicant name, document summary, per-rule compliance outcomes, overall recommendation, confidence score, subsidy tier, and a UTC timestamp
  - Returns the report as a structured object
  - Emits `M5.achieved: decision report generated — case ID: <id>, recommendation: <result>` on success
  - Emits `M5.missed: decision report generation failed — case ID: <id>` on failure

### Agent System Prompt

- [x] Write the agent system prompt in `assets/apartment-subsidy-eligibility-agent/app/agent.py` that instructs the agent to:
  - Greet the case worker and ask for the applicant's country code, program code, and documents
  - Execute the eligibility check pipeline: ingest → validate → compliance check → assessment → report
  - Never fabricate extracted data; relay tool errors verbatim
  - Always present the recommendation with supporting evidence and confidence score
  - Route low-confidence results (< 70) to a human case worker with explanation
  - Never write to any external system — the agent is read-only except for report generation

---

## MCP Tool Integration (Path A — API spec available)

- [x] API spec file exists at `specification/apartment-subsidy-eligibility-agent/api-specs/legal-document.edmx` (SAP S/4HANA Legal Document API, ORD ID: `sap.s4:apiResource:CE_LEGAL_DOCUMENT_0001:v1`)
- [x] Invoke `mcp-translation-file` skill to generate MCP translation artifacts from `specification/apartment-subsidy-eligibility-agent/api-specs/legal-document.edmx`
- [x] Invoke `setup-solution` skill to create and register the MCP server asset
- [x] Read the generated `asset.yaml` to extract the exact `ordId` value for the MCP server
- [x] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module
- [x] Add MCP server dependency to `assets/apartment-subsidy-eligibility-agent/asset.yaml` under `requires` using the exact ORD ID from the generated asset
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill

---

## Business Instrumentation

- [x] Implement business step instrumentation for each milestone M1–M5: structured logging with pattern `[MILESTONE_ID].[achieved|missed]: [description]` and OpenTelemetry custom spans using decorator form on regular async methods and context manager form in non-generator async functions
- [x] Extract all business logic from `stream()` into a plain async helper `_run_agent()` to avoid `GeneratorExit` span errors
- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## Testing

- [x] `conftest.py` only sets `IBD_TESTING=true` — mock MCP tools are loaded from `mcp-mock.json`
- [x] Write unit tests in `assets/apartment-subsidy-eligibility-agent/tests/`:
  - `test_ingest_documents.py` — test document ingestion with complete and incomplete document sets
  - `test_validate_documents.py` — test field extraction and expiry validation (mock LLM)
  - `test_check_legal_compliance.py` — test rule evaluation against sample `de.json` rule set
  - `test_assess_subsidy_eligibility.py` — test recommendation logic at various confidence levels
  - `test_generate_decision_report.py` — test report assembly and timestamp
- [x] Write one integration test `tests/test_agent_flow.py` exercising the full pipeline with mocked LLM and MCP tools
- [x] Run `pytest` from `assets/apartment-subsidy-eligibility-agent/` (no args) — coverage must be ≥ 70%
- [x] Verify `assets/apartment-subsidy-eligibility-agent/app/agent.py` has exactly 9 decorated functions — run `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/apartment-subsidy-eligibility-agent/app/agent.py` and confirm it returns 9
- [x] Run `pytest` again (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/apartment-subsidy-eligibility-agent/`
