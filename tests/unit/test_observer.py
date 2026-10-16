from slidekick.contracts import SessionEvent, SessionEventType, SessionState
from slidekick.observer import EventPublisher


def make_event(
    event_type=SessionEventType.STARTED,
    previous_state=SessionState.IDLE,
    new_state=SessionState.RUNNING,
    use_case="UC10",
):
    return SessionEvent(
        type=event_type,
        previous_state=previous_state,
        new_state=new_state,
        use_case=use_case,
    )


class RecordingObserver:
    def __init__(self, log=None, name=None):
        self.events = []
        self._log = log
        self._name = name

    def update(self, event):
        self.events.append(event)
        if self._log is not None:
            self._log.append(self._name)


def test_subscriber_receives_published_event():
    publisher = EventPublisher()
    observer = RecordingObserver()
    publisher.subscribe(observer)
    event = make_event()

    publisher.publish(event)

    assert observer.events == [event]


def test_every_subscriber_receives_the_same_event():
    publisher = EventPublisher()
    first = RecordingObserver()
    second = RecordingObserver()
    publisher.subscribe(first)
    publisher.subscribe(second)
    event = make_event()

    publisher.publish(event)

    assert first.events == [event]
    assert second.events == [event]
    assert first.events[0] is second.events[0]


def test_subscribers_are_notified_in_subscription_order():
    log = []
    publisher = EventPublisher()
    publisher.subscribe(RecordingObserver(log, "first"))
    publisher.subscribe(RecordingObserver(log, "second"))
    publisher.subscribe(RecordingObserver(log, "third"))

    publisher.publish(make_event())

    assert log == ["first", "second", "third"]


def test_events_are_delivered_in_publish_order():
    publisher = EventPublisher()
    observer = RecordingObserver()
    publisher.subscribe(observer)
    started = make_event()
    paused = make_event(
        SessionEventType.PAUSED, SessionState.RUNNING, SessionState.PAUSED, "UC6"
    )

    publisher.publish(started)
    publisher.publish(paused)

    assert observer.events == [started, paused]


def test_unsubscribed_observer_receives_no_later_events_but_keeps_earlier_ones():
    publisher = EventPublisher()
    observer = RecordingObserver()
    publisher.subscribe(observer)
    before = make_event()
    after = make_event(
        SessionEventType.PAUSED, SessionState.RUNNING, SessionState.PAUSED, "UC6"
    )

    publisher.publish(before)
    publisher.unsubscribe(observer)
    publisher.publish(after)

    assert observer.events == [before]


def test_unsubscribing_one_observer_leaves_the_others_subscribed():
    publisher = EventPublisher()
    removed = RecordingObserver()
    kept = RecordingObserver()
    publisher.subscribe(removed)
    publisher.subscribe(kept)

    publisher.unsubscribe(removed)
    publisher.publish(make_event())

    assert removed.events == []
    assert len(kept.events) == 1


def test_subscribing_the_same_observer_twice_delivers_each_event_once():
    publisher = EventPublisher()
    observer = RecordingObserver()
    publisher.subscribe(observer)
    publisher.subscribe(observer)

    publisher.publish(make_event())

    assert len(observer.events) == 1


def test_unsubscribing_an_observer_that_was_never_subscribed_is_a_no_op():
    publisher = EventPublisher()
    subscribed = RecordingObserver()
    publisher.subscribe(subscribed)

    publisher.unsubscribe(RecordingObserver())
    publisher.publish(make_event())

    assert len(subscribed.events) == 1


def test_publishing_with_no_subscribers_does_nothing():
    EventPublisher().publish(make_event())


def test_observer_can_unsubscribe_itself_while_being_notified():
    # publish iterates over a copy, so removing an observer mid-publish
    # must not make a later observer miss the event.
    publisher = EventPublisher()
    later = RecordingObserver()

    class OneShotObserver:
        def __init__(self):
            self.events = []

        def update(self, event):
            self.events.append(event)
            publisher.unsubscribe(self)

    one_shot = OneShotObserver()
    publisher.subscribe(one_shot)
    publisher.subscribe(later)

    publisher.publish(make_event())
    publisher.publish(make_event())

    assert len(one_shot.events) == 1
    assert len(later.events) == 2
