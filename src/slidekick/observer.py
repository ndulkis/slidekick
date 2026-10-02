"""Publish/subscribe boundary so session events can reach multiple
consumers (UI, recognition, presentation adapter) without the session
controller depending on any of them directly.
"""

from typing import Protocol

from .contracts import SessionEvent


class Observer(Protocol):
    def update(self, event: SessionEvent) -> None: ...


class EventPublisher:
    def __init__(self) -> None:
        self._observers: list[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def publish(self, event: SessionEvent) -> None:
        for observer in list(self._observers):
            observer.update(event)
