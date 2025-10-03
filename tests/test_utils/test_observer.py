from datetime import datetime

from bigdata_research_tools.utils.observer import (
    OberserverNotification,
    Observable,
    Observer,
)


class TestObserver(Observer):
    def __init__(self):
        self.notifications = []

    def update(self, message: OberserverNotification):
        self.notifications.append(message)


def test_observer_notification_model():
    ts = datetime.now().isoformat()
    msg = {"foo": "bar"}
    notification = OberserverNotification(timestamp=ts, message=msg)
    assert notification.timestamp == ts
    assert notification.message == msg


def test_observable_register_and_notify():
    observable = Observable()
    observer1 = TestObserver()
    observer2 = TestObserver()
    observable.register_observer(observer1)
    observable.register_observer(observer2)
    message = "test message"
    observable.notify_observers(message)
    assert len(observer1.notifications) == 1
    assert len(observer2.notifications) == 1
    assert observer1.notifications[0].message == message
    assert observer2.notifications[0].message == message
    assert isinstance(observer1.notifications[0].timestamp, str)


def test_observable_unregister():
    observable = Observable()
    observer = TestObserver()
    observable.register_observer(observer)
    observable.notify_observers("first message")
    assert len(observer.notifications) == 1
    observable.unregister_observer(observer)
    observable.notify_observers("should not be received")
    assert len(observer.notifications) == 1  # No new notifications after unregistering
