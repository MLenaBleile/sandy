"""Event bus for real-time communication between agent and dashboard.

This module provides a simple pub/sub event system for notifying the dashboard
of agent lifecycle events (sandwich creation, foraging progress, etc.).
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)


# Event type constants
SANDWICH_CREATED = "sandwich.created"
FORAGING_STARTED = "foraging.started"
FORAGING_COMPLETED = "foraging.completed"
VALIDATION_SCORED = "validation.scored"
INGREDIENT_IDENTIFIED = "ingredient.identified"
SESSION_STATE_CHANGED = "session.state_changed"


@dataclass
class Event:
    """Represents a single event in the system."""

    event_type: str
    data: Dict[str, Any]
    timestamp: datetime


class EventBus:
    """Simple in-memory pub/sub event bus.

    Provides event publishing and subscription capabilities with event history
    for polling-based updates. Events are stored in a fixed-size deque for
    memory efficiency.

    Example usage:
        # Create event bus
        bus = EventBus()

        # Subscribe to events
        def on_sandwich(data):
            print(f"New sandwich: {data['name']}")

        bus.subscribe(SANDWICH_CREATED, on_sandwich)

        # Publish events
        bus.publish(SANDWICH_CREATED, {
            'sandwich_id': str(uuid4()),
            'name': 'The Squeeze',
            'validity_score': 0.95
        })

        # Poll for recent events
        last_check = datetime.now() - timedelta(seconds=10)
        recent = bus.get_events_since(last_check)
    """

    def __init__(self, max_history: int = 1000):
        """Initialize event bus.

        Args:
            max_history: Maximum number of events to keep in history (default 1000)
        """
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._events_queue: deque[Event] = deque(maxlen=max_history)
        self._max_history = max_history

    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to a specific event type.

        Args:
            event_type: The event type to subscribe to (e.g., SANDWICH_CREATED)
            callback: Function to call when event is published. Receives event data dict.
        """
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}, total subscribers: {len(self._subscribers[event_type])}")

    def unsubscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unsubscribe from a specific event type.

        Args:
            event_type: The event type to unsubscribe from
            callback: The callback function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for {event_type}")

    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to all subscribers.

        The event is added to the event history and all registered callbacks
        are invoked. If a callback raises an exception, it is logged but does
        not prevent other callbacks from executing.

        Args:
            event_type: The type of event being published
            data: Event payload (must be JSON-serializable for dashboard consumption)
        """
        event = Event(event_type=event_type, data=data, timestamp=datetime.now())
        self._events_queue.append(event)

        logger.debug(f"Published {event_type} with data: {data}")

        # Notify all subscribers
        for callback in self._subscribers.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Event callback failed for {event_type}: {e}", exc_info=True)

    def get_events_since(self, timestamp: datetime, event_type: str = None) -> List[Event]:
        """Get all events that occurred after a specific timestamp.

        Used for polling-based updates (e.g., dashboard refresh every 2 seconds).

        Args:
            timestamp: Return only events newer than this
            event_type: Optional filter for specific event type

        Returns:
            List of Event objects matching the criteria
        """
        events = [e for e in self._events_queue if e.timestamp > timestamp]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events

    def get_recent_events(self, limit: int = 100, event_type: str = None) -> List[Event]:
        """Get the N most recent events.

        Args:
            limit: Maximum number of events to return
            event_type: Optional filter for specific event type

        Returns:
            List of Event objects, most recent first
        """
        events = list(self._events_queue)

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        # Return most recent first
        return list(reversed(events[-limit:]))

    def clear_history(self) -> None:
        """Clear all events from history."""
        self._events_queue.clear()
        logger.info("Event history cleared")

    def get_subscriber_count(self, event_type: str = None) -> int:
        """Get count of subscribers.

        Args:
            event_type: Specific event type, or None for total across all types

        Returns:
            Number of subscribers
        """
        if event_type:
            return len(self._subscribers.get(event_type, []))
        else:
            return sum(len(subs) for subs in self._subscribers.values())


# Global event bus instance (can be initialized in main)
_global_event_bus: EventBus = None


def get_global_event_bus() -> EventBus:
    """Get or create the global event bus instance.

    Returns:
        The global EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def set_global_event_bus(event_bus: EventBus) -> None:
    """Set the global event bus instance.

    Args:
        event_bus: EventBus instance to use globally
    """
    global _global_event_bus
    _global_event_bus = event_bus
