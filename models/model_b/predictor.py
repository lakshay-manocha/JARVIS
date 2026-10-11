
"""
predictor.py
Independent inference API for Model B:
Stored-State vs Current-State Mismatch Classifier.

Strictly decoupled from the JARVIS orchestration engine.
"""

import json
import math
import os
from typing import Any, Dict, List, Set, Tuple

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


# ============================================================
# Configuration
# ============================================================

MODEL_VERSION = "JARVIS-StateMismatch-v1.0"
DEFAULT_THRESHOLD = 0.30
MAX_LENGTH = 128

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Support both the current layout and a nested model directory.
NESTED_MODEL_DIR = os.path.join(
    CURRENT_DIR, "jarvis_state_mismatch_model"
)

MODEL_DIR = (
    NESTED_MODEL_DIR
    if os.path.isdir(NESTED_MODEL_DIR)
    else CURRENT_DIR
)

ENCODER_DIR = os.path.join(MODEL_DIR, "model")
TOKENIZER_DIR = os.path.join(MODEL_DIR, "tokenizer")
CLASSIFIER_HEAD_PATH = os.path.join(
    MODEL_DIR, "classifier", "classifier_head.pt"
)
THRESHOLD_FILE = os.path.join(MODEL_DIR, "threshold.json")

# This implementation uses CPU inference for compatibility.
DEVICE = torch.device("cpu")


# ============================================================
# Threshold loading and validation
# ============================================================

def _load_threshold(path: str) -> float:
    """
    Load and validate the selected classification threshold.

    A missing configuration file uses DEFAULT_THRESHOLD.
    A present but malformed configuration raises an error.
    """
    if not os.path.isfile(path):
        return DEFAULT_THRESHOLD

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("The JSON root must be an object.")

        if "selected_threshold" not in data:
            raise ValueError(
                "Missing required key 'selected_threshold'."
            )

        threshold = float(data["selected_threshold"])

    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid Model B threshold configuration: {path}. "
            "Expected a numeric 'selected_threshold' between 0 and 1."
        ) from exc

    if not math.isfinite(threshold) or not 0.0 <= threshold <= 1.0:
        raise ValueError(
            "Model B selected_threshold must be finite and between "
            f"0 and 1. Received: {threshold!r}"
        )

    return threshold


THRESHOLD = _load_threshold(THRESHOLD_FILE)


# ============================================================
# Model architecture
# ============================================================

class SiameseInferenceClassifier(nn.Module):
    """
    Siamese encoder with a binary classification head.

    Pair representation:
        [u, v, abs(u - v), u * v]

    The trained classifier checkpoint is mandatory.
    """

    def __init__(
        self,
        encoder_dir: str,
        head_weights_path: str,
    ) -> None:
        super().__init__()

        if not os.path.isdir(encoder_dir):
            raise FileNotFoundError(
                f"Model B encoder directory was not found: {encoder_dir}"
            )

        if not os.path.isfile(
            os.path.join(encoder_dir, "config.json")
        ):
            raise FileNotFoundError(
                f"Missing encoder config.json in: {encoder_dir}"
            )

        if not os.path.isfile(head_weights_path):
            raise FileNotFoundError(
                "Model B classifier checkpoint is missing: "
                f"{head_weights_path}. Refusing to use random weights."
            )

        try:
            self.encoder = AutoModel.from_pretrained(
                encoder_dir,
                local_files_only=True,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Could not load the local Model B encoder: {encoder_dir}"
            ) from exc

        emb_dim = self.encoder.config.hidden_size
        pair_dim = 4 * emb_dim

        self.classifier = nn.Sequential(
            nn.Linear(pair_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 1),
        )

        # Load only tensor-based checkpoint data.
        try:
            state_dict = torch.load(
                head_weights_path,
                map_location="cpu",
                weights_only=True,
            )
        except Exception as exc:
            raise RuntimeError(
                "Could not safely load the Model B classifier checkpoint: "
                f"{head_weights_path}"
            ) from exc

        # Support checkpoints wrapped in {"state_dict": ...}.
        if isinstance(state_dict, dict) and "state_dict" in state_dict:
            state_dict = state_dict["state_dict"]

        if not isinstance(state_dict, dict) or not state_dict:
            raise RuntimeError(
                "The Model B classifier checkpoint is empty or invalid."
            )

        try:
            self.classifier.load_state_dict(
                state_dict,
                strict=True,
            )
        except (RuntimeError, TypeError) as exc:
            raise RuntimeError(
                "The Model B classifier checkpoint is incompatible with "
                "the classifier architecture. Verify the trained head "
                "and model version."
            ) from exc

        self.to(DEVICE)
        self.eval()

    @staticmethod
    def _mean_pooling(
        model_output: Any,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Mean-pool token embeddings using the attention mask."""
        token_embeddings = model_output[0]

        expanded_mask = (
            attention_mask.unsqueeze(-1)
            .expand(token_embeddings.size())
            .to(dtype=token_embeddings.dtype)
        )

        summed_embeddings = torch.sum(
            token_embeddings * expanded_mask,
            dim=1,
        )

        summed_mask = torch.clamp(
            expanded_mask.sum(dim=1),
            min=1e-9,
        )

        return summed_embeddings / summed_mask

    def encode(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Encode one batch of text sequences."""
        output = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        return self._mean_pooling(output, attention_mask)

    def forward(
        self,
        u_ids: torch.Tensor,
        u_mask: torch.Tensor,
        v_ids: torch.Tensor,
        v_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Return raw mismatch logits for a pair of states."""
        u = self.encode(u_ids, u_mask)
        v = self.encode(v_ids, v_mask)

        difference = torch.abs(u - v)
        product = u * v

        pair_representation = torch.cat(
            [u, v, difference, product],
            dim=-1,
        )

        return self.classifier(pair_representation).squeeze(-1)


# ============================================================
# Lazy model initialization
# ============================================================

_LOADED_TOKENIZER = None
_LOADED_MODEL = None


def _get_model() -> Tuple[Any, SiameseInferenceClassifier]:
    """
    Load Model B from local assets once.

    No implicit remote-model download or random-head fallback is allowed.
    Global caches are updated only after successful initialization.
    """
    global _LOADED_TOKENIZER, _LOADED_MODEL

    if _LOADED_MODEL is not None and _LOADED_TOKENIZER is not None:
        return _LOADED_TOKENIZER, _LOADED_MODEL

    required_paths = {
        "encoder directory": ENCODER_DIR,
        "tokenizer directory": TOKENIZER_DIR,
        "classifier checkpoint": CLASSIFIER_HEAD_PATH,
    }

    for description, path in required_paths.items():
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Required Model B {description} is missing: {path}"
            )

    if not os.path.isdir(ENCODER_DIR):
        raise FileNotFoundError(
            f"Model B encoder is not a directory: {ENCODER_DIR}"
        )

    if not os.path.isdir(TOKENIZER_DIR):
        raise FileNotFoundError(
            f"Model B tokenizer is not a directory: {TOKENIZER_DIR}"
        )

    if not os.path.isfile(
        os.path.join(TOKENIZER_DIR, "tokenizer.json")
    ):
        raise FileNotFoundError(
            "Model B tokenizer.json is missing from: "
            f"{TOKENIZER_DIR}"
        )

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            TOKENIZER_DIR,
            local_files_only=True,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Could not load the local Model B tokenizer: {TOKENIZER_DIR}"
        ) from exc

    model = SiameseInferenceClassifier(
        encoder_dir=ENCODER_DIR,
        head_weights_path=CLASSIFIER_HEAD_PATH,
    )

    # Publish cached objects only after all initialization succeeds.
    _LOADED_TOKENIZER = tokenizer
    _LOADED_MODEL = model

    return _LOADED_TOKENIZER, _LOADED_MODEL


# ============================================================
# State serialization
# ============================================================

def _format_field(value: Any) -> str:
    """Convert a state field to a stable, readable string."""
    if value is None:
        return "NOT_AVAILABLE"

    if isinstance(value, str):
        if value.strip().upper() == "NOT_AVAILABLE":
            return "NOT_AVAILABLE"
        return value

    if isinstance(value, list):
        if not value:
            return "NONE"

        return ", ".join(str(item) for item in value)

    return str(value)


def serialize_state(state: dict) -> str:
    """
    Serialize a state dictionary into the Model B input format.

    The field names and ordering are kept consistent with the
    original inference API.
    """
    if not isinstance(state, dict):
        raise TypeError(
            "State must be a dictionary; "
            f"received {type(state).__name__}."
        )

    return (
        f"APPLICATIONS: {_format_field(state.get('applications'))} | "
        f"FILES: {_format_field(state.get('files'))} | "
        f"BROWSER TABS: {_format_field(state.get('browser_tabs'))} | "
        f"PROCESSES: {_format_field(state.get('processes'))} | "
        f"COMPLETED SUBTASKS: "
        f"{_format_field(state.get('completed_subtasks'))}"
    )


# ============================================================
# Deterministic changed-resource extraction
# ============================================================

def _resource_set(state: dict, key: str) -> Set[str]:
    """
    Extract comparable resource identifiers.

    Non-list and unavailable fields are treated as unknown, not as
    evidence that every resource is missing or newly added.
    """
    value = state.get(key)

    if not isinstance(value, list):
        return set()

    # String conversion also ensures all set entries are hashable.
    return {str(item) for item in value if item is not None}


def extract_changed_resources(
    stored_state: dict,
    current_state: dict,
) -> List[Dict[str, str]]:
    """
    Report observable differences between supported resource lists.

    This deterministic output is independent of the classifier score.
    """
    if not isinstance(stored_state, dict):
        raise TypeError("stored_state must be a dictionary.")

    if not isinstance(current_state, dict):
        raise TypeError("current_state must be a dictionary.")

    changed: List[Dict[str, str]] = []

    resource_fields = [
        ("applications", "APPLICATION"),
        ("files", "FILE"),
        ("browser_tabs", "BROWSER_TAB"),
        ("processes", "PROCESS"),
        ("completed_subtasks", "COMPLETED_SUBTASK"),
    ]

    for field, resource_type in resource_fields:
        stored_items = _resource_set(stored_state, field)
        current_items = _resource_set(current_state, field)

        for identifier in sorted(stored_items - current_items):
            changed.append({
                "type": resource_type,
                "identifier": identifier,
                "change": "MISSING",
            })

        for identifier in sorted(current_items - stored_items):
            changed.append({
                "type": resource_type,
                "identifier": identifier,
                "change": "ADDED",
            })

    return changed


# ============================================================
# Public inference API
# ============================================================

def predict_state_mismatch(
    stored_state: dict,
    current_state: dict,
) -> dict:
    """
    Predict whether the stored and current states mismatch.

    Returns:
        {
            "mismatch": bool,
            "probability": float,
            "confidence": float,
            "threshold": float,
            "changed_resources": list[dict],
            "model_version": str
        }

    Probability is the model's estimated mismatch probability.
    Confidence is the probability associated with the predicted class;
    it is not a guarantee of calibration.
    """
    if not isinstance(stored_state, dict):
        raise TypeError("stored_state must be a dictionary.")

    if not isinstance(current_state, dict):
        raise TypeError("current_state must be a dictionary.")

    tokenizer, model = _get_model()

    stored_text = serialize_state(stored_state)
    current_text = serialize_state(current_state)

    try:
        stored_tokens = tokenizer(
            stored_text,
            max_length=MAX_LENGTH,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        current_tokens = tokenizer(
            current_text,
            max_length=MAX_LENGTH,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        with torch.inference_mode():
            logits = model(
                stored_tokens["input_ids"].to(DEVICE),
                stored_tokens["attention_mask"].to(DEVICE),
                current_tokens["input_ids"].to(DEVICE),
                current_tokens["attention_mask"].to(DEVICE),
            )

            logit = float(logits.reshape(-1)[0].item())

            if not math.isfinite(logit):
                raise RuntimeError(
                    f"Model B produced a non-finite logit: {logit!r}"
                )

            probability = float(
                torch.sigmoid(torch.tensor(logit, dtype=torch.float32)).item()
            )

    except Exception as exc:
        if isinstance(exc, RuntimeError) and str(exc).startswith(
            "Model B produced a non-finite logit"
        ):
            raise

        raise RuntimeError(
            "Model B inference failed while comparing stored and current "
            "states. Check the local model assets and input data."
        ) from exc

    if not math.isfinite(probability):
        raise RuntimeError(
            f"Model B produced an invalid probability: {probability!r}"
        )

    mismatch = bool(probability >= THRESHOLD)

    confidence = (
        probability if mismatch else 1.0 - probability
    )

    changed_resources = extract_changed_resources(
        stored_state,
        current_state,
    )

    return {
        "mismatch": mismatch,
        "probability": round(probability, 4),
        "confidence": round(confidence, 4),
        "threshold": round(THRESHOLD, 4),
        "changed_resources": changed_resources,
        "model_version": MODEL_VERSION,
    }


# ============================================================
# Standalone smoke test
# ============================================================

if __name__ == "__main__":
    sample_stored = {
        "applications": ["Visual Studio Code"],
        "files": ["/home/user/Desktop/project.py"],
        "browser_tabs": "NOT_AVAILABLE",
        "processes": ["code /home/user/Desktop/project.py"],
        "completed_subtasks": "NOT_AVAILABLE",
        "timestamp": None,
        "resource_identities": ["app:vscode"],
    }

    sample_current = {
        "applications": ["Google Chrome"],
        "files": "NOT_AVAILABLE",
        "browser_tabs": ["https://google.com"],
        "processes": "NOT_AVAILABLE",
        "completed_subtasks": "NOT_AVAILABLE",
        "timestamp": None,
        "resource_identities": ["app:chrome"],
    }

    result = predict_state_mismatch(
        sample_stored,
        sample_current,
    )

    print("Inference Test Result:")
    print(json.dumps(result, indent=2))