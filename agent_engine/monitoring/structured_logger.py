"""Phase F-5: structured orchestration logging."""

from __future__ import annotations

import json
import logging
from typing import Any


class StructuredLogger:
    """Small JSON logger adapter used by the orchestrator.

    The standard-library logger remains the transport.  This class only
    defines a stable structured payload so a later monitoring backend can
    consume the same events without changing orchestration code.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("jarvis.agent_engine")

    def log(self, level: int, event: str, **fields: Any) -> None:
        payload = {"event": event, **fields}
        self.logger.log(level, json.dumps(payload, default=str, sort_keys=True))

    def info(self, event: str, **fields: Any) -> None:
        self.log(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self.log(logging.WARNING, event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self.log(logging.ERROR, event, **fields)
