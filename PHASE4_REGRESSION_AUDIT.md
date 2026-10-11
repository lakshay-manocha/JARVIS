# JARVIS Phase 4 — Regression and Acceptance Audit

## Status

**In progress — integration regression passes; full project-wide closure is pending.**

Phase 4 is intended to run the full suite, classify failures versus environment/setup problems, audit AC-01 through AC-16, and record final closure. This audit was run in a Linux analysis environment against the current project archive. The developer's target environment is Windows, so Linux-only path-semantics failures must be confirmed on Windows before they are treated as product defects.

## Verification results

| Verification | Result | Interpretation |
|---|---:|---|
| Integration suite | **114 passed, 0 failed** | Reconfirmed after Phase 4 edits |
| Acceptance criteria + Phase 2/3 hardening + graph validation integration tests | **54 passed, 0 failed** | Targeted regression passes |
| Broad suite with platform-dependent and real-browser test modules excluded | **1,540 passed, 7 failed** | Useful partial signal; not a full-suite pass |
| Initial full-suite collection | **Blocked by 8 collection errors** | `pynput` was absent from the analysis environment; it is listed in `requirements.txt` |
| Real Playwright browser tests | **Blocked by missing Chromium executable** | Python Playwright is not enough; install Chromium separately |

The broad filtered run's seven failures are:

1. Three `FakeFileSystemBackend` tests that use Windows drive paths. The backend currently uses platform-dependent `pathlib.PurePath`; on Linux, `C:\\Temp\\...` is not parsed as a Windows path. Confirm these on Windows before deciding whether to make path parsing platform-independent.
2. Three Phase E transition tests expect `PENDING -> RUNNING` to be rejected, but `StateTransitionPolicy` explicitly allows it. This is a conflict between the current policy and test expectations. Phase E is frozen; no state-transition code was changed.
3. One Phase E resume test expects `InvalidStateTransitionError` when resuming a task without a checkpoint, but the current implementation raises `KeyError` for the missing checkpoint first. Phase E is frozen; no StateManager code was changed.

The graph cycle test initially failed because the validator's message said “Circular dependency” while the test searched for the word “cycle”. The diagnostic was clarified to say “Cycle detected: circular dependency…”. The graph test now passes. No graph-validation algorithm behavior was changed.

Warnings are predominantly existing Pydantic v2 class-based `Config` deprecations and `datetime.utcnow()` deprecations. These warnings did not fail the integration suite and have not been mass-refactored during this verification phase.

## Dependency/setup update

`requirements.txt` now includes `playwright>=1.40,<2.0`; `pynput` was already listed. After installing Python dependencies, run:

```bat
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Playwright browser binaries are downloaded separately from Python packages. If a project uses real desktop automation, run the relevant tests only in an environment where those OS interactions are intended and safe.

## Acceptance criteria audit

| Criterion | Phase 4 status | Evidence / next action |
|---|---|---|
| AC-01 | PASS | Acceptance-criteria test suite passes |
| AC-02 | PASS | Acceptance-criteria test suite passes |
| AC-03 | PASS | Acceptance-criteria test suite passes |
| AC-04 | PASS | Acceptance-criteria test suite passes |
| AC-05 | PASS | Acceptance-criteria test suite passes |
| AC-06 | PASS | Model A advisory boundary test passes |
| AC-07 | PASS | Model B evidence boundary test passes |
| AC-08 | PASS | Deterministic state-difference tests pass |
| AC-09 | PASS | Explicit guard policy tests pass |
| AC-10 | PASS | Logging-mode tests pass |
| AC-11 | PASS | Warning-mode tests pass |
| AC-12 | PASS | Decision-pathway tests pass |
| AC-13 | PARTIAL | Architecture/regression checks pass; final full-suite confirmation pending |
| AC-14 | OPEN | Full project-wide suite has not completed successfully in this environment |
| AC-15 | PASS | 37 Phase 2/3 hardening tests pass; integration suite has 114 passes |
| AC-16 | PASS | Architecture and known limitations are documented in `INTEGRATION_GUIDE.md` and the completion report |

The AC-01–AC-12 test module plus Phase 2/3 hardening tests and graph validation tests produced **54 passed** in the current run. AC-14 is intentionally not marked passed until the full Windows suite is run with its required dependencies and browser binaries installed.

## Frozen Phase E boundary

No changes were made to `StateManager`, `DecisionStateBridge`, or `StateTransitionPolicy`. The transition-test conflict and missing-checkpoint exception mismatch are recorded for a deliberate decision rather than silently altering the frozen implementation.

## Required Windows verification

From the project root, with the project virtual environment activated:

```bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m pytest agent_engine\tests\integration\ -q
python -m pytest -q
```

If the full suite fails, capture the complete summary and traceback. Classify failures into: (1) missing Python dependency, (2) missing browser/system asset, (3) OS-specific path/automation behavior, (4) frozen Phase E policy/test-contract conflict, and (5) confirmed regression. Do not change Phase E until the user explicitly approves unfreezing it or a minimal integration defect is proven.

## Files changed in Phase 4 so far

- `requirements.txt` — added Playwright Python dependency.
- `agent_engine/agent_brain/graph_validator.py` — clarified cycle diagnostic wording to match the existing test contract.
- `INTEGRATION_GUIDE.md` — added a Phase 4 audit pointer.
- `PHASE4_REGRESSION_AUDIT.md` — this audit report.
