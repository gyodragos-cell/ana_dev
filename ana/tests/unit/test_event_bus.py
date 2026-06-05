from ana.core.event_bus.bus import EventBus, EventLog


def test_event_bus_publish_subscribe_and_replay():
    bus = EventBus(replay_limit=3)
    log = EventLog()
    bus.subscribe("*", log.record)

    first = bus.publish("runtime.started", {"ok": True}, trace_id="t1")
    second = bus.publish("runtime.finished", {"ok": True}, trace_id="t1")

    assert first.sequence == 1
    assert second.sequence == 2
    assert [event["topic"] for event in log.events] == [
        "runtime.started",
        "runtime.finished",
    ]
    assert [event.topic for event in bus.replay()] == [
        "runtime.started",
        "runtime.finished",
    ]
    assert [event.topic for event in bus.replay("runtime.finished")] == [
        "runtime.finished"
    ]
