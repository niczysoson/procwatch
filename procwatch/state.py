"""Process state tracking for procwatch supervisors."""

from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
from typing import Optional


class ProcessState(Enum):
    """Enumeration of possible process lifecycle states."""
    PENDING = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    STOPPED = auto()
    FAILED = auto()
    BACKOFF = auto()


@dataclass
class StateTransition:
    """Records a single state change event."""
    from_state: ProcessState
    to_state: ProcessState
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None

    def __str__(self) -> str:
        ts = self.timestamp.isoformat()
        base = f"[{ts}] {self.from_state.name} -> {self.to_state.name}"
        if self.reason:
            base += f" ({self.reason})"
        return base


class StateTracker:
    """Tracks the current state and transition history of a managed process."""

    # Valid transitions: maps from_state -> set of allowed to_states
    _VALID_TRANSITIONS: dict = {
        ProcessState.PENDING:  {ProcessState.STARTING},
        ProcessState.STARTING: {ProcessState.RUNNING, ProcessState.FAILED},
        ProcessState.RUNNING:  {ProcessState.STOPPING, ProcessState.FAILED},
        ProcessState.STOPPING: {ProcessState.STOPPED},
        ProcessState.STOPPED:  {ProcessState.STARTING},
        ProcessState.FAILED:   {ProcessState.BACKOFF, ProcessState.STARTING, ProcessState.STOPPED},
        ProcessState.BACKOFF:  {ProcessState.STARTING, ProcessState.STOPPED},
    }

    def __init__(self) -> None:
        self._state = ProcessState.PENDING
        self._history: list[StateTransition] = []

    @property
    def current(self) -> ProcessState:
        return self._state

    @property
    def history(self) -> list[StateTransition]:
        return list(self._history)

    def transition(self, to_state: ProcessState, reason: Optional[str] = None) -> StateTransition:
        """Attempt a state transition. Raises ValueError on invalid transition."""
        allowed = self._VALID_TRANSITIONS.get(self._state, set())
        if to_state not in allowed:
            raise ValueError(
                f"Invalid transition: {self._state.name} -> {to_state.name}"
            )
        event = StateTransition(
            from_state=self._state,
            to_state=to_state,
            reason=reason,
        )
        self._history.append(event)
        self._state = to_state
        return event

    def is_terminal(self) -> bool:
        """Return True if the process is in a terminal (non-restartable) state."""
        return self._state == ProcessState.STOPPED
