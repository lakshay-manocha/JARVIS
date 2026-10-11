# JARVIS Phase 1 Merge Manifest

## Merge policy
- Stable `JARVIS(1).zip` is the authoritative baseline.
- Existing stable paths were preserved byte-for-byte.
- Only paths absent from the stable archive were added from `JARVIS_Model_Integration.zip`.
- Existing overlapping automation files, `decision_state_bridge.py`, existing integration tests, and `agent_engine/main.py` were not overwritten.
- The integration ZIP's `agent_engine/integration/__init__.py` exports were not copied over the stable empty file in Phase 1. Import-time eager loading could pull both predictors into the package import path before the collision-safe loader work in a later phase. Explicit module imports remain available.
- Cache files and compiled Python bytecode from the integration ZIP were not added.

## Added in Phase 1
- Model A and Model B integration adapters
- Workflow advisory planner
- Environment snapshot collector and stored-state mapper
- Deterministic checker and Consistency Guard
- Integration feature flags and workflow state service
- Model A and Model B model/tokenizer/classifier assets and supporting metadata
- Four new integration test modules
- `INTEGRATION_GUIDE.md`

## Intentionally not merged from integration ZIP
- Overlapping paths: stable versions retained.
- `demo.py`: remains in the reference ZIP; not part of the stable runtime integration.
- `agent_engine/main.py`: stable version retained.
- Integration package `__init__.py`: stable version retained for now; exports can be reviewed after import safety is addressed.

## Important
This artifact completes file-level Phase 1 only. It does not claim that runtime wiring, predictor import isolation, DecisionManager routing, provider integration, or tests are already fixed. Those belong to subsequent implementation phases.
