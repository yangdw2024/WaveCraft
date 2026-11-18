#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
from typing import Dict, List, Callable, Any, Optional
from enum import Enum


class EventPriority(Enum):
    HIGHEST = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    LOWEST = 4


class Event:
    def __init__(self, event_type: str, data: Any = None, source: str = "",
                 priority: EventPriority = EventPriority.NORMAL):
        self.event_type = event_type
        self.data = data
        self.source = source
        self.priority = priority
        self.timestamp = time.time()


class EventBus:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._subscribers: Dict[str, List[Dict]] = {}
        self._global_subscribers: List[Dict] = []
        self._lock = threading.Lock()
        self._enabled = True
        self._initialized = True

    def publish(self, event_type: str, data: Any = None, source: str = "",
                priority: EventPriority = EventPriority.NORMAL) -> int:
        if not self._enabled:
            return 0

        event = Event(event_type=event_type, data=data, source=source, priority=priority)
        handlers = []

        with self._lock:
            for pattern in list(self._subscribers.keys()):
                if self._matches_pattern(pattern, event_type):
                    for sub in self._subscribers[pattern]:
                        handlers.append(sub)

            for sub in self._global_subscribers:
                handlers.append(sub)

        handlers.sort(key=lambda h: h["priority"].value)

        notified = 0
        for handler in handlers:
            try:
                handler["callback"](event)
                notified += 1
            except Exception:
                pass

        return notified

    def subscribe(self, pattern: str, callback: Callable[[Event], None],
                  priority: EventPriority = EventPriority.NORMAL):
        with self._lock:
            if pattern not in self._subscribers:
                self._subscribers[pattern] = []
            self._subscribers[pattern].append({
                "callback": callback,
                "priority": priority,
            })

    def subscribe_global(self, callback: Callable[[Event], None],
                        priority: EventPriority = EventPriority.NORMAL):
        with self._lock:
            self._global_subscribers.append({
                "callback": callback,
                "priority": priority,
            })

    def unsubscribe(self, pattern: str, callback: Callable):
        with self._lock:
            if pattern in self._subscribers:
                self._subscribers[pattern] = [
                    s for s in self._subscribers[pattern] if s["callback"] != callback
                ]

    def unsubscribe_global(self, callback: Callable):
        with self._lock:
            self._global_subscribers = [
                s for s in self._global_subscribers if s["callback"] != callback
            ]

    def _matches_pattern(self, pattern: str, event_type: str) -> bool:
        if pattern == "*":
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return event_type.startswith(prefix)
        if pattern == event_type:
            return True
        return False

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False


class EventBusMixin:
    def __init__(self):
        self._event_bus = EventBus()

    def publish_event(self, event_type: str, data: Any = None, source: str = "",
                      priority: EventPriority = EventPriority.NORMAL):
        self._event_bus.publish(event_type, data, source, priority)

    def subscribe_event(self, pattern: str, callback: Callable[[Event], None],
                       priority: EventPriority = EventPriority.NORMAL):
        self._event_bus.subscribe(pattern, callback, priority)