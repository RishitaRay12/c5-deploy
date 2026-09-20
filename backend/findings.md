I’ll trace the exposed FastAPI endpoint from the route into orchestration, tools, persistence, and tests, then exercise the cheapest available validation path against the capstone requirements. I’ll keep the report grounded in the current implementation and summarize each requirement as met, partial, or missing with evidence and recommendations.

Search complete: Trace backend requirements

Searched codebase for "FastAPI main API endpoint Retail Policy Intelligence capstone", 15 results

Searched codebase for "API endpoint route request response models authentication RBAC routing orchestration RAG SQL persistence audit logging", 19 results

Searched for files matching `**/main*.py`, 1 match

Searched for regex `FastAPI|app.* =.*FastAPI`, 17 results

Searched for files matching `**/router*.py`, no matches

No matches found. Your search pattern might be excluded completely by either the search.exclude settings or .*ignore files.
If you believe that it should have results, you can check into the .*ignore files and the exclude setting (here are some excluded patterns for reference:[**/node_modules,**/bower_components,**/*.code-search]).
Then if you want to include those files you can call the tool again by setting "includeIgnoredFiles" to true.

Searched for files matching `**/requirements*.md`, no matches

Searched for files matching `**/test*.py`, 2 matches

Read , lines 1 to 260

Read 

Read 

Read 

Read 

Read 

Read , lines 40 to 99

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

Read 

The main endpoint is `POST /chat`. The local path already shows several important gaps before runtime testing: the response model omits risk, confidence, validation, and escalation fields; high-risk handling is delegated to an LLM heuristic; and the SQL/RAG workers are not visibly enforcing the route selected by the classifier for customers. I’m checking the project’s test/runtime setup now, then I’ll run the narrowest executable validation and separate environment failures from implementation failures.

Read 

Read 

Read 

Read 

The surrounding implementation confirms the escalation payload is built internally but discarded at the API boundary, so a client cannot verify the capstone’s trust and human-review requirements. The existing tests also appear outdated (`files` versus the live `single_file` upload contract) and invoke the real graph, so I’m running them to document the actual baseline rather than assuming they pass.

Ran terminal command: pytest -q
Completed with input: pytest -q

Ran terminal command: pytest -q tests.py
Completed with input: pytest -q tests.py

The executable baseline is currently blocked before test collection by an environment dependency incompatibility: `llama_parse` pulls a Pydantic v1 model that fails under the installed Python 3.14 stack. This is separate from endpoint correctness. I’m doing a focused static/API contract check next so the report can still distinguish runtime readiness, contract compliance, and design gaps.

Ran terminal command: ruff check main.py schema.py app
Completed with input: ruff check main.py schema.py app

Ran terminal command: python -m compileall -q main.py schema.py app rag.py sql_data.py

Ran terminal command: git status --short

Read , lines 1 to 120

Syntax compilation passes, while focused lint reports pre-existing style issues across the app rather than an endpoint syntax defect. The validation picture is now clear: the API is protected and wired to a LangGraph flow, but the public contract and several safety guarantees required by the capstone are incomplete or unreliable. I’m doing one final check of the exact response schema and test mismatches so the recommendations are precise and prioritized.

Searched for regex `risk_level|confidence_score|human_handoff|audit_log|trace_id|conversation history|legal hold|restricted jurisdiction|conflicting policy` (`**/*.py`), 55 results

Read , lines 130 to 255

Read 

Read , lines 70 to 120

## Backend API Validation Report

**Endpoint reviewed:** `POST /chat` in `main.py:171`

| Requirement | Status | Evidence / Justification | Recommendation |
|---|---|---|---|
| Authentication | Partial | `/chat` uses JWT authentication through `get_current_user`. | Add integration tests for missing, expired, malformed, and revoked tokens. |
| Role-based access control | **Fail** | User role is inferred from query text by the LLM, not from the authenticated user record. | Store roles in `users`; authorize employee/customer access server-side. |
| Intelligent routing | Partial | Classifier supports direct, RAG, SQL, and hybrid routes in `classifier.py:14`. | Add deterministic routing safeguards and route-level tests. |
| RAG integration | Pass | RAG retrieval returns source, page, and snippet metadata in `rag.py:27`. | Add retrieval quality and citation accuracy tests. |
| SQL integration | Partial | SQL agent can query required compliance tables in `rag.py:12`. | Restrict generated SQL to read-only queries and expose validated SQL results in the API response. |
| Multi-agent orchestration | Partial | LangGraph includes classifier, workers, validator, synthesizer, evaluator, and handoff nodes in `graph.py:40`. | Add explicit plan/reason/act state and verify every required agent workflow. |
| Risk classification | Partial | Validator assigns low, medium, or high risk in `validator.py:36`. | Expand detection to all eight mandatory high-risk scenarios and test paraphrased cases. |
| High-risk escalation | **Fail** | High-risk requests can be blocked and still pass the evaluator without human escalation. Escalation mainly depends on an LLM handoff tool. | Force escalation whenever `risk_level == "high"`, confidence is below threshold, or legal validation is requested. |
| Mandatory scenarios | **Fail** | Handoff prompt covers six scenarios but omits conflicting policy clauses and some required cases; detection is non-deterministic. | Implement deterministic rules plus LLM semantic detection for all mandatory scenarios. |
| Confidence and trust metadata | **Fail** | Scores are calculated and sent to Langfuse, but `ChatResponse` only returns answer, sources, and token usage in `schema.py:44`. | Return `risk_level`, `confidence_score`, `validation_result`, `human_handoff`, and evaluator feedback. |
| Source attribution | Partial | RAG sources are returned, but SQL validation output and policy citations are not exposed. | Return structured source types, SQL evidence, document references, and uncertainty disclosure. |
| Human handoff context | **Fail** | Handoff includes only the current query and generated answer in `human_handoff.py:83`. | Include conversation history, retrieved documents, SQL results, user identity, risk flags, and trace ID. |
| Auditability | Partial | Chat messages are persisted and Langfuse observations are recorded. | Persist routing, risk, confidence, escalation, sources, SQL results, and decision timestamps in an audit table. |
| Multi-turn context | Partial | LangGraph checkpoints and chat history exist, but the synthesizer uses only the current query. | Load relevant prior messages into the agent state and add context continuity tests. |
| PII protection | Partial | Some sensitive-data patterns are blocked in `validator.py:7`. | Add output scanning, redaction, structured PII tests, and database access controls. |
| SLO compliance | **Fail** | No measured TSR, P95 latency, SQL accuracy, PII leakage, cost, or misclassification metrics are implemented. | Add automated evaluation datasets, latency instrumentation, dashboards, and release thresholds. |
| API test readiness | **Fail** | `pytest -q` discovers no tests. `pytest -q tests.py` fails during collection because `llama_parse` is incompatible with the installed Python 3.14/Pydantic stack. | Rename to `test_*.py`, isolate optional PDF parsing imports, and use a supported Python/dependency combination. |
| Upload endpoint contract | **Fail** | Live endpoint expects `single_file`; existing test sends `files`. | Update the test or restore the documented multi-file contract. |
| Syntax | Pass | `compileall` completed successfully for the API and orchestration modules. | Keep compile/type checks in CI. |

## Overall Verdict

The backend has a promising LangGraph foundation and working authentication, persistence, RAG, SQL, scoring, and handoff components. However, `POST /chat` does **not yet satisfy the capstone production requirements** because critical decision metadata is hidden, RBAC is inferred from user input, high-risk escalation is not guaranteed, and SLO/test validation is absent.

**Priority improvements:**

1. Enforce authenticated roles server-side.
2. Guarantee escalation for all high-risk conditions.
3. Expand the `ChatResponse` contract with risk, confidence, validation, and handoff metadata.
4. Persist complete audit and handoff context.
5. Repair test discovery and dependency compatibility before measuring SLOs.

Validation completed: Python compilation passed; the existing API test suite could not collect because of the `llama_parse`/Pydantic compatibility error.