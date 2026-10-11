import pytest
from pydantic import ValidationError

from agent_engine.state_mismatch.state_mismatch_contract import (
    ChangedResource,
    ResourceChange,
    ResourceType,
    StateMismatchQuery,
    StateMismatchResult,
    StateSnapshot,
)


def make_valid_state() -> dict:
    return {
        "applications": ["Google Chrome", "Visual Studio Code"],
        "files": ["report.pdf", "notes.txt"],
        "browser_tabs": ["https://example.com"],
        "processes": ["chrome.exe"],
        "completed_subtasks": ["open_browser"],
        "timestamp": 1720000000.0,
        "resource_identities": [
            "APPLICATION:Google Chrome",
            "FILE:report.pdf",
        ],
    }


def test_valid_state_snapshot_is_accepted():
    state = StateSnapshot(**make_valid_state())

    assert state.applications == [
        "Google Chrome",
        "Visual Studio Code",
    ]
    assert state.files == ["report.pdf", "notes.txt"]


def test_state_snapshot_supports_not_available():
    state = StateSnapshot(
        applications="NOT_AVAILABLE",
        files="NOT_AVAILABLE",
        browser_tabs="NOT_AVAILABLE",
        processes="NOT_AVAILABLE",
        completed_subtasks="NOT_AVAILABLE",
    )

    assert state.applications == "NOT_AVAILABLE"
    assert state.files == "NOT_AVAILABLE"


def test_state_snapshot_rejects_invalid_collection_type():
    with pytest.raises(ValidationError):
        StateSnapshot(applications=123)


def test_state_snapshot_rejects_non_string_collection_items():
    with pytest.raises(ValidationError):
        StateSnapshot(applications=["Chrome", 123])


def test_state_snapshot_rejects_extra_fields():
    with pytest.raises(ValidationError):
        StateSnapshot(
            **make_valid_state(),
            unexpected_field="invalid",
        )


def test_state_snapshot_accepts_optional_timestamp():
    state_data = make_valid_state()
    state_data["timestamp"] = None

    state = StateSnapshot(**state_data)

    assert state.timestamp is None

def test_state_snapshot_rejects_invalid_timestamp():
    state_data = make_valid_state()
    state_data["timestamp"] = "invalid"

    with pytest.raises(ValidationError):
        StateSnapshot(**state_data)

def test_state_mismatch_query_accepts_two_states():
    query = StateMismatchQuery(
        stored_state=make_valid_state(),
        current_state=make_valid_state(),
    )

    assert query.stored_state.applications == [
        "Google Chrome",
        "Visual Studio Code",
    ]
    assert query.current_state.files == [
        "report.pdf",
        "notes.txt",
    ]


def test_state_mismatch_query_requires_stored_state():
    with pytest.raises(ValidationError):
        StateMismatchQuery(
            current_state=make_valid_state(),
        )


def test_state_mismatch_query_requires_current_state():
    with pytest.raises(ValidationError):
        StateMismatchQuery(
            stored_state=make_valid_state(),
        )


def test_state_mismatch_query_rejects_extra_fields():
    with pytest.raises(ValidationError):
        StateMismatchQuery(
            stored_state=make_valid_state(),
            current_state=make_valid_state(),
            extra_field="invalid",
        )


def test_valid_changed_resource_is_accepted():
    resource = ChangedResource(
        type=ResourceType.APPLICATION,
        identifier="Google Chrome",
        change=ResourceChange.ADDED,
    )

    assert resource.type == ResourceType.APPLICATION
    assert resource.identifier == "Google Chrome"
    assert resource.change == ResourceChange.ADDED


def test_changed_resource_accepts_string_enum_values():
    resource = ChangedResource(
        type="FILE",
        identifier="report.pdf",
        change="MISSING",
    )

    assert resource.type == ResourceType.FILE
    assert resource.change == ResourceChange.MISSING


def test_changed_resource_rejects_invalid_resource_type():
    with pytest.raises(ValidationError):
        ChangedResource(
            type="INVALID_TYPE",
            identifier="Chrome",
            change="ADDED",
        )


def test_changed_resource_rejects_invalid_change_type():
    with pytest.raises(ValidationError):
        ChangedResource(
            type="APPLICATION",
            identifier="Chrome",
            change="MODIFIED",
        )


def test_changed_resource_rejects_blank_identifier():
    with pytest.raises(ValidationError):
        ChangedResource(
            type="APPLICATION",
            identifier="   ",
            change="ADDED",
        )


def test_changed_resource_rejects_empty_identifier():
    with pytest.raises(ValidationError):
        ChangedResource(
            type="APPLICATION",
            identifier="",
            change="ADDED",
        )


def test_changed_resource_rejects_extra_fields():
    with pytest.raises(ValidationError):
        ChangedResource(
            type="APPLICATION",
            identifier="Chrome",
            change="ADDED",
            extra_field="invalid",
        )


def test_valid_state_mismatch_result_is_accepted():
    result = StateMismatchResult(
        mismatch=True,
        probability=0.9818,
        confidence=0.9818,
        threshold=0.30,
        changed_resources=[
            {
                "type": "APPLICATION",
                "identifier": "Google Chrome",
                "change": "ADDED",
            }
        ],
        model_version="JARVIS-StateMismatch-v1.0",
    )

    assert result.mismatch is True
    assert result.probability == 0.9818
    assert result.confidence == 0.9818
    assert result.threshold == 0.30
    assert len(result.changed_resources) == 1


def test_state_mismatch_result_accepts_empty_changed_resources():
    result = StateMismatchResult(
        mismatch=False,
        probability=0.12,
        confidence=0.88,
        threshold=0.30,
        changed_resources=[],
        model_version="JARVIS-StateMismatch-v1.0",
    )

    assert result.mismatch is False
    assert result.changed_resources == []


@pytest.mark.parametrize(
    "field_name",
    ["probability", "confidence", "threshold"],
)
def test_probability_confidence_threshold_reject_values_above_one(
    field_name,
):
    payload = {
        "mismatch": True,
        "probability": 0.5,
        "confidence": 0.5,
        "threshold": 0.30,
        "changed_resources": [],
        "model_version": "JARVIS-StateMismatch-v1.0",
    }

    payload[field_name] = 1.1

    with pytest.raises(ValidationError):
        StateMismatchResult(**payload)


@pytest.mark.parametrize(
    "field_name",
    ["probability", "confidence", "threshold"],
)
def test_probability_confidence_threshold_reject_values_below_zero(
    field_name,
):
    payload = {
        "mismatch": True,
        "probability": 0.5,
        "confidence": 0.5,
        "threshold": 0.30,
        "changed_resources": [],
        "model_version": "JARVIS-StateMismatch-v1.0",
    }

    payload[field_name] = -0.1

    with pytest.raises(ValidationError):
        StateMismatchResult(**payload)


def test_state_mismatch_result_rejects_invalid_changed_resource():
    with pytest.raises(ValidationError):
        StateMismatchResult(
            mismatch=True,
            probability=0.9,
            confidence=0.9,
            threshold=0.30,
            changed_resources=[
                {
                    "type": "INVALID",
                    "identifier": "Chrome",
                    "change": "ADDED",
                }
            ],
            model_version="JARVIS-StateMismatch-v1.0",
        )


def test_state_mismatch_result_rejects_blank_model_version():
    with pytest.raises(ValidationError):
        StateMismatchResult(
            mismatch=True,
            probability=0.9,
            confidence=0.9,
            threshold=0.30,
            changed_resources=[],
            model_version="   ",
        )


def test_state_mismatch_result_rejects_extra_fields():
    with pytest.raises(ValidationError):
        StateMismatchResult(
            mismatch=True,
            probability=0.9,
            confidence=0.9,
            threshold=0.30,
            changed_resources=[],
            model_version="JARVIS-StateMismatch-v1.0",
            extra_field="invalid",
        )