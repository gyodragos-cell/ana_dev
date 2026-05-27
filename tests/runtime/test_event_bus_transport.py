"""Tests for distributed event bus transport publishing."""

from core.event_bus import EventBus


class FakeTransport:
    """In-memory transport for event bus tests."""

    def __init__(self):
        """Initialize sent envelope storage."""
        self.sent = []

    def send(self, envelope):
        """Record one envelope."""
        self.sent.append(envelope)


def test_publish_local_only_does_not_send_over_transport():
    """local_only=True should prevent transport broadcast."""
    transport = FakeTransport()
    bus = EventBus(transport=transport, node_id="n1")
    bus.publish("test.topic", {"x": 1}, local_only=True)
    assert len(transport.sent) == 0


def test_publish_sends_event_publish_over_transport():
    """Publish should send event.publish when transport is configured."""
    transport = FakeTransport()
    bus = EventBus(transport=transport, node_id="n1")
    bus.publish("test.topic", {"x": 1})
    assert len(transport.sent) == 1
    envelope = transport.sent[0]
    assert envelope["type"] == "event.publish"
    assert envelope["payload"]["topic"] == "test.topic"
    assert envelope["payload"]["origin_node"] == "n1"


def test_handle_event_message_calls_local_subscribers():
    """Remote event envelopes should deliver to local subscribers."""
    transport = FakeTransport()
    bus = EventBus(transport=transport, node_id="n0")
    received = []
    bus.subscribe("test.topic", lambda data: received.append(data))
    envelope = {
        "version": 1,
        "type": "event.publish",
        "source_node": "n2",
        "target_node": "n0",
        "timestamp": "2025-01-01T00:00:00Z",
        "payload": {
            "topic": "test.topic",
            "data": {"y": 2},
            "origin_node": "n2",
        },
    }
    bus.handle_event_message(envelope)
    assert received == [{"y": 2}]


def test_handle_event_message_does_not_rebroadcast():
    """Remote event handling should stay local to avoid loops."""
    transport = FakeTransport()
    bus = EventBus(transport=transport, node_id="n0")
    envelope = {
        "version": 1,
        "type": "event.publish",
        "source_node": "n2",
        "target_node": "n0",
        "timestamp": "2025-01-01T00:00:00Z",
        "payload": {
            "topic": "test.topic",
            "data": {"z": 3},
            "origin_node": "n2",
        },
    }
    bus.handle_event_message(envelope)
    assert len(transport.sent) == 0


def test_publish_without_transport_still_notifies_local_subscribers():
    """Local subscribers should receive events without transport."""
    bus = EventBus(transport=None, node_id="n1")
    received = []
    bus.subscribe("test.topic", lambda data: received.append(data))
    bus.publish("test.topic", {"x": 1})
    assert received == [{"x": 1}]
