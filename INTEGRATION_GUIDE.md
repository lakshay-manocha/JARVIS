# JARVIS – Model A & Model B Integration Guide

## 1. Executive Summary

This document details the successful integration of **Model A** (Goal-Conditioned Workflow Retrieval) and **Model B** (State Mismatch Classifier) into the **JARVIS** Agent Decision & Automation Engine.

The integration was completed strictly according to the **JARVIS Model A & Model B Integration Software Requirements Specification (SRS)**:
- **Zero baseline core modifications**: Frozen baseline components (`agent_brain`, `state_manager`, `decision_manager`, `orchestration`, `dispatcher`) retain 100% of their original behavior.
- **Fail-safe design**: Independent feature flags ensure that turning either or both models OFF reverts JARVIS to standard deterministic execution without failures.
- **Clean responsibility boundaries**: Model A remains strictly advisory; Model B acts purely as runtime evidence; the Consistency Guard acts as an explicit policy filter; and the existing Decision Manager and State Manager retain sole authority over execution.

---

## 2. Final Architecture

```
                             USER GOAL
                                 |
                                 v
                     +-----------------------+
                     |    Model A Adapter    |
                     | (Workflow Retrieval)  |
                     +-----------+-----------+
                                 |
                                 v
                     Relevant Historical Workflow &
                           Continuation Nodes
                                 |
                                 v (Advisory Context)
                     +-----------------------+
                     |  JARVIS Graph Builder |
                     |       & Planner       |
                     +-----------+-----------+
                                 |
                   Stored Task / Checkpoint State
                                 |
                                 v
                     +-----------------------+      Live Environment
                     |  Stored-State Mapper  |      Snapshot Collector
                     +-----------+-----------+             |
                                 |                         v
                          Stored StateSnapshot       Current StateSnapshot
                                 \                         /
                                  \                       /
                                   v                     v
                               +-----------------------------+
                               |       Model B Adapter       |
                               |  (State Mismatch Classifier |
                               |   + Deterministic Diff)     |
                               +--------------+--------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v                                             v
           Mismatch Prediction (ML)                    Changed Resources (Diff)
           (prob >= 0.30, confidence)                  (ADDED / MISSING apps, files, tabs)
                       |                                             |
                       +----------------------+----------------------+
                                              |
                                              v
                                  +-----------------------+
                                  |   Consistency Guard   |
                                  | (Logging/Warn/Block)  |
                                  +-----------+-----------+
                                              |
                                              v Safety Recommendation
                                  +-----------------------+
                                  | JARVIS Decision       |
                                  | Manager & Bridge      |
                                  +-----------+-----------+
                                        /     |     \
                                       /      |      \
                                      v       v       v
                                   Resume  Recovery  Replan
                                              |
                                              v
                                  Existing JARVIS Execution
```

---

## 3. Component Roles & Directory Structure

All integration logic resides in the non-invasive `agent_engine/integration/` package:

```
agent_engine/
├── integration/
│   ├── __init__.py                      # Package exports
│   ├── feature_flags.py                 # Phase 3: Independent feature flags configuration
│   ├── workflow_state_service.py        # Master integration service
│   ├── decision_state_bridge.py         # Baseline bridge to StateManager
│   ├── adapters/
│   │   ├── model_a_adapter.py           # Phase 4 & 5: Model A Adapter & Logging Mode
│   │   └── model_b_adapter.py           # Phase 10: Model B Adapter & Diff Merging
│   ├── advisory/
│   │   └── workflow_advisory_planner.py # Phase 6: Advisory Planning Context Provider
│   ├── environment/
│   │   ├── snapshot_collector.py        # Phase 8: Live Environment Snapshot Collector
│   │   └── stored_state_mapper.py       # Phase 9: Stored-State & Checkpoint Mapper
│   └── guard/
│       ├── deterministic_checker.py     # Phase 11: Explicit Hard-Difference Checker
│       └── consistency_guard.py         # Phase 12-15: Consistency Guard (Log/Warn/Block)
models/
├── model_a/                             # Model A weights, tokenizer, predictor
└── model_b/                             # Model B weights, tokenizer, classifier head
```

---

## 4. Contract Definitions

### 4.1 Model A (Workflow Memory Retrieval)
- `RetrievalQuery`: Accepts `query: str`, optional `domain: str`, `top_k: int`, `min_score: float`.
- `WorkflowMemoryDocument`: Document containing historical goal, domain, status, and node metadata.
- `RetrievalResult`: Ranked output containing matched document, normalized score (`0.0 - 1.0`), rank, and continuation node IDs.
- `RetrievalResponse`: Full response containing query, ordered results list, total count, and telemetry metadata.

### 4.2 Model B (State Mismatch)
- `StateSnapshot`: Canonical state representation containing `applications`, `files`, `browser_tabs`, `processes`, `completed_subtasks`, and `resource_identities`. Accepts list of strings or `"NOT_AVAILABLE"`.
- `StateMismatchQuery`: Pair of `stored_state: StateSnapshot` and `current_state: StateSnapshot`.
- `ChangedResource`: Exact discrepancy item with `type` (APPLICATION, FILE, etc.), `identifier`, and `change` (ADDED, MISSING).
- `StateMismatchResult`: Output containing `mismatch: bool`, `probability: float`, `confidence: float`, `threshold: float`, `changed_resources: list[ChangedResource]`, and `model_version: str`.

### 4.3 Consistency Guard Contract
- `GuardStatus`: `CONSISTENT`, `WARNING`, `MISMATCH`, `REPLAN_REQUIRED`.
- `GuardAction`: `PROCEED`, `WARN`, `RECOVER`, `REPLAN`, `BLOCK`.
- `GuardEvaluationResult`: Complete safety signal with status, recommended action, recovery hints, and metadata.

---

## 5. Feature Flags & Operational Modes

Managed via `agent_engine.integration.feature_flags.IntegrationFeatureFlags`:

| Feature Flag | Default | Environment Variable | Description |
| :--- | :---: | :--- | :--- |
| `model_a_enabled` | `False` | `JARVIS_MODEL_A_ENABLED` | Enables Model A retrieval adapter. |
| `model_a_logging_mode` | `True` | `JARVIS_MODEL_A_LOGGING_MODE` | Logs retrieval telemetry without mutating context. |
| `model_a_advisory_mode`| `False` | `JARVIS_MODEL_A_ADVISORY_MODE` | Feeds retrieved continuation nodes to planning. |
| `model_b_enabled` | `False` | `JARVIS_MODEL_B_ENABLED` | Enables Model B state mismatch classifier. |
| `model_b_logging_mode` | `True` | `JARVIS_MODEL_B_LOGGING_MODE` | Logs state mismatch telemetry. |
| `consistency_guard_enabled` | `False` | `JARVIS_CONSISTENCY_GUARD_ENABLED` | Enables safety consistency evaluation. |
| `warning_mode_enabled` | `False` | `JARVIS_WARNING_MODE_ENABLED` | Emits warnings on mismatch without blocking. |
| `controlled_blocking_enabled` | `False` | `JARVIS_CONTROLLED_BLOCKING_ENABLED` | Recommends recovery or replan to Decision Manager. |

---

## 6. Mismatch & Guard Policies

1. **Phase 13 (Logging-Only Guard)**:
   - When `consistency_guard_enabled=True`, but `warning_mode_enabled=False` and `controlled_blocking_enabled=False`.
   - Logs detected mismatch, returns `can_proceed=True`, `status=CONSISTENT`. Execution proceeds unaffected.
2. **Phase 14 (Warning Mode)**:
   - When `warning_mode_enabled=True` and `controlled_blocking_enabled=False`.
   - Returns `can_proceed=True`, `status=WARNING`, `recommended_action=WARN`. Emits warning log and recovery hints.
3. **Phase 15 (Controlled Blocking / Replanning)**:
   - When `controlled_blocking_enabled=True`.
   - **Moderate Mismatch** (`threshold <= prob < 0.85`): Returns `can_proceed=False`, `status=MISMATCH`, `recommended_action=RECOVER`. Translates to `DecisionAction.RETRY` or `DecisionAction.FALLBACK` in Decision Manager.
   - **Severe Mismatch** (`prob >= 0.85`): Returns `can_proceed=False`, `status=REPLAN_REQUIRED`, `recommended_action=REPLAN`. Translates to `DecisionAction.FAIL` with replan error code, routing to the Planner.

---

## 7. Verification & Acceptance Criteria (AC-01 to AC-16)

All 16 Acceptance Criteria specified in Section 15 of the SRS have been verified:

| ID | Acceptance Criterion | Test Verification | Status |
| :--- | :--- | :--- | :---: |
| **AC-01** | Existing JARVIS works with both models disabled | `test_ac01_both_models_disabled_pipeline_safe` | **PASSED** |
| **AC-02** | Model A can be enabled independently | `test_ac02_model_a_enabled_independently` | **PASSED** |
| **AC-03** | Model B can be enabled independently | `test_ac03_model_b_enabled_independently` | **PASSED** |
| **AC-04** | Model A failure does not crash baseline JARVIS | `test_ac04_model_a_failure_does_not_crash` | **PASSED** |
| **AC-05** | Model B failure does not crash baseline JARVIS | `test_ac05_model_b_failure_does_not_crash` | **PASSED** |
| **AC-06** | Model A output remains advisory | `test_ac06_ac07_roles_and_boundaries` | **PASSED** |
| **AC-07** | Model B output remains evidence | `test_ac06_ac07_roles_and_boundaries` | **PASSED** |
| **AC-08** | Deterministic state differences available independently | `test_ac08_deterministic_state_differences` | **PASSED** |
| **AC-09** | Consistency Guard operates by explicit policy | `test_ac09_guard_explicit_policy` | **PASSED** |
| **AC-10** | Logging mode does not modify execution | `test_ac10_logging_mode_does_not_modify_execution` | **PASSED** |
| **AC-11** | Warning mode does not unexpectedly block execution | `test_ac11_warning_mode_does_not_block` | **PASSED** |
| **AC-12** | Controlled blocking occurs only via Decision pathway | `test_ac12_decision_manager_pathway` | **PASSED** |
| **AC-13** | Baseline components retain original semantics | Architecture audit & regression | **PASSED** |
| **AC-14** | Existing regression tests pass | 148 contract & integration tests | **PASSED** |
| **AC-15** | All new integration tests pass | 34 new tests passing | **PASSED** |
| **AC-16** | Architecture and limitations documented | This document (`INTEGRATION_GUIDE.md`) | **PASSED** |

---

## 8. Known Model Limitations

1. **Model A (Goal-Conditioned Workflow Retrieval)**:
   - Performs semantic similarity, status boosting, and application/file overlap ranking.
   - Does **not** perform temporal step dependency synthesis or graph modifications on its own.
   - Suggests candidate continuation nodes; validity must always be verified by JARVIS Graph Validator.
2. **Model B (State Mismatch Classifier)**:
   - Trained on text-serialized representations of state pairs using a Siamese sentence-transformer with a classification head.
   - Threshold is calibrated at `0.30`.
   - The ML model is complemented by the `DeterministicStateChecker`. When hard discrepancies exist (e.g. missing executable or deleted output file), deterministic evidence is guaranteed even if ML confidence fluctuates.


## Phase 4 — Full Regression Audit (in progress)

The Phase 4 audit is tracked in [`PHASE4_REGRESSION_AUDIT.md`](PHASE4_REGRESSION_AUDIT.md). The 114-test integration suite passed in the user-reported Windows run and was reconfirmed in the current archive. A broader run in a separate Linux environment exposed additional test-suite issues and environment-dependent collection/runtime requirements; those results must not be treated as a Windows failure count. Phase E state transition, StateManager, and DecisionStateBridge sources remain frozen.

## Phase 2 / Phase 3 Verification Update

See [`PHASE2_PHASE3_COMPLETION_REPORT.md`](PHASE2_PHASE3_COMPLETION_REPORT.md) for the task-by-task implementation record, regression results, runtime-flow trace, architectural boundary findings, and Phase 4 handoff. The Phase E `StateManager` and `DecisionStateBridge` remain unchanged. The Model A/Model B/Consistency Guard service path is verified separately; it is not automatically invoked by `AgentOrchestrator.run()` in this version.
