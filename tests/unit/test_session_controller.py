import dataclasses

import pytest

from slidekick.contracts import SessionEvent, SessionEventType, SessionState
from slidekick.session_controller import InvalidTransitionError, SessionController

# The transition tables in docs/session-state-model.md are the source of
# truth for everything below.

# Public operations that reach each state, starting from a new controller.
PATH_TO_STATE = {
    SessionState.IDLE: [],
    SessionState.RUNNING: ["start"],
    SessionState.PAUSED: ["start", "pause"],
    SessionState.ENDED: ["start", "end"],
}


class RecordingObserver:
    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)


def controller_in(state):
    controller = SessionController()
    for operation in PATH_TO_STATE[state]:
        getattr(controller, operation)()
    return controller


def test_new_controller_starts_idle():
    assert SessionController().state is SessionState.IDLE


@pytest.mark.parametrize(
    ("from_state", "operation", "to_state", "event_type", "use_case"),
    [
        (
            SessionState.IDLE,
            "start",
            SessionState.RUNNING,
            SessionEventType.STARTED,
            "UC10",
        ),
        (
            SessionState.RUNNING,
            "pause",
            SessionState.PAUSED,
            SessionEventType.PAUSED,
            "UC6",
        ),
        (
            SessionState.PAUSED,
            "resume",
            SessionState.RUNNING,
            SessionEventType.RESUMED,
            "UC7",
        ),
        (
            SessionState.RUNNING,
            "end",
            SessionState.ENDED,
            SessionEventType.ENDED,
            "UC8",
        ),
        # Restart is drawn in the state diagram as UC10 from ended back to running.
        (
            SessionState.ENDED,
            "start",
            SessionState.RUNNING,
            SessionEventType.STARTED,
            "UC10",
        ),
    ],
)
def test_valid_transition_changes_state_and_publishes_event(
    from_state, operation, to_state, event_type, use_case
):
    controller = controller_in(from_state)
    observer = RecordingObserver()
    controller.subscribe(observer)

    returned = getattr(controller, operation)()

    expected = SessionEvent(
        type=event_type,
        previous_state=from_state,
        new_state=to_state,
        use_case=use_case,
    )
    assert controller.state is to_state
    assert returned == expected
    assert observer.events == [expected]


@pytest.mark.parametrize(
    ("from_state", "operation"),
    [
        (SessionState.IDLE, "pause"),
        (SessionState.IDLE, "resume"),
        (SessionState.IDLE, "end"),
        (SessionState.RUNNING, "start"),
        (SessionState.RUNNING, "resume"),
        (SessionState.PAUSED, "start"),
        (SessionState.PAUSED, "pause"),
        (SessionState.ENDED, "pause"),
        (SessionState.ENDED, "resume"),
        (SessionState.ENDED, "end"),
    ],
)
def test_invalid_transition_is_rejected_without_side_effects(from_state, operation):
    controller = controller_in(from_state)
    observer = RecordingObserver()
    controller.subscribe(observer)

    with pytest.raises(InvalidTransitionError):
        getattr(controller, operation)()

    assert controller.state is from_state
    assert observer.events == []


def test_end_from_paused_is_rejected():
    # The state diagram has no edge from paused to ended, so a paused
    # session must be resumed first. This is the open question in
    # docs/session-state-model.md. If the team allows ending from paused,
    # change this test together with SessionController.end.
    controller = controller_in(SessionState.PAUSED)
    observer = RecordingObserver()
    controller.subscribe(observer)

    with pytest.raises(InvalidTransitionError):
        controller.end()

    assert controller.state is SessionState.PAUSED
    assert observer.events == []


def test_rejection_message_names_the_operation_and_the_state():
    with pytest.raises(InvalidTransitionError, match="Cannot pause session from idle"):
        SessionController().pause()


def test_full_lifecycle_publishes_events_in_order():
    controller = SessionController()
    observer = RecordingObserver()
    controller.subscribe(observer)

    controller.start()
    controller.pause()
    controller.resume()
    controller.end()
    controller.start()

    assert [event.type for event in observer.events] == [
        SessionEventType.STARTED,
        SessionEventType.PAUSED,
        SessionEventType.RESUMED,
        SessionEventType.ENDED,
        SessionEventType.STARTED,
    ]
    assert controller.state is SessionState.RUNNING


def test_each_event_chains_from_the_previous_one_and_describes_a_change():
    controller = SessionController()
    observer = RecordingObserver()
    controller.subscribe(observer)

    controller.start()
    controller.pause()
    controller.resume()
    controller.end()

    assert observer.events[0].previous_state is SessionState.IDLE
    for earlier, later in zip(observer.events, observer.events[1:], strict=False):
        assert later.previous_state is earlier.new_state
    for event in observer.events:
        assert event.previous_state is not event.new_state


def test_state_cannot_be_assigned_from_outside():
    # Regression guard: state is a read-only property backed by _state.
    # An earlier version assigned to the property inside _transition, which
    # made every transition raise AttributeError.
    controller = SessionController()

    with pytest.raises(AttributeError):
        controller.state = SessionState.RUNNING

    assert controller.state is SessionState.IDLE


def test_unsubscribed_observer_is_not_notified_by_the_controller():
    controller = SessionController()
    observer = RecordingObserver()
    controller.subscribe(observer)
    controller.start()

    controller.unsubscribe(observer)
    controller.pause()

    assert [event.type for event in observer.events] == [SessionEventType.STARTED]


def test_controllers_do_not_share_state_or_subscribers():
    first = SessionController()
    second = SessionController()
    observer = RecordingObserver()
    first.subscribe(observer)

    first.start()

    assert second.state is SessionState.IDLE
    second.start()
    assert [event.type for event in observer.events] == [SessionEventType.STARTED]


def test_event_returned_by_a_transition_is_immutable():
    event = SessionController().start()

    with pytest.raises(dataclasses.FrozenInstanceError):
        event.new_state = SessionState.IDLE
