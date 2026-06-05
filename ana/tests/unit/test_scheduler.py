import pytest

from ana.core.error_model.errors import ValidationError
from ana.core.scheduler.scheduler import DeterministicScheduler, ScheduledTask


def test_scheduler_orders_dependencies_deterministically():
    scheduler = DeterministicScheduler()
    ordered = scheduler.order(
        [
            ScheduledTask("orchestrator", ("event_bus", "error_model")),
            ScheduledTask("error_model"),
            ScheduledTask("event_bus", ("error_model",)),
        ]
    )

    assert ordered == ["error_model", "event_bus", "orchestrator"]


def test_scheduler_fails_fast_on_cycles():
    scheduler = DeterministicScheduler()

    with pytest.raises(ValidationError):
        scheduler.order(
            [
                ScheduledTask("a", ("b",)),
                ScheduledTask("b", ("a",)),
            ]
        )
