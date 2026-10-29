import dataclasses

import pytest

from slidekick.contracts import SessionEvent, SessionEventType, SessionState


def test_session_state_values_match_the_state_model():
    assert {state.value for state in SessionState} == {
        "idle",
        "running",
        "paused",
        "ended",
    }


def test_session_event_type_values_match_the_event_contract():
    assert {event_type.value for event_type in SessionEventType} == {
        "session_started",
        "session_paused",
        "session_resumed",
        "session_ended",
    }


def test_session_event_exposes_the_documented_fields():
    assert [field.name for field in dataclasses.fields(SessionEvent)] == [
        "type",
        "previous_state",
        "new_state",
        "use_case",
    ]


def test_session_event_compares_by_value():
    def build():
        return SessionEvent(
            type=SessionEventType.PAUSED,
            previous_state=SessionState.RUNNING,
            new_state=SessionState.PAUSED,
            use_case="UC6",
        )

    assert build() == build()


def test_session_event_is_immutable():
    event = SessionEvent(
        type=SessionEventType.STARTED,
        previous_state=SessionState.IDLE,
        new_state=SessionState.RUNNING,
        use_case="UC10",
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        event.use_case = "UC6"
