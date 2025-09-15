from typing import Any
from datetime import datetime

from abc import ABC, abstractmethod

from pydantic import BaseModel

class OberserverNotification(BaseModel):
    timestamp: str
    message: Any

class Observer(ABC):
    @abstractmethod
    def update(self, message: OberserverNotification):
        pass


class Observable(ABC):
    def __init__(self):
        self.observers = []
    
    def register_observer(self, observer: Observer):
        self.observers.append(observer)

    def unregister_observer(self, observer: Observer):
        self.observers.remove(observer)
    
    def notify_observers(self, message: Any):
        ts = datetime.now().isoformat()
        notification = OberserverNotification(timestamp=ts, message=message)
        for observer in self.observers:
            observer.update(notification)
