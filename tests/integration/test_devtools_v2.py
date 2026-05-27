"""DevTools v2 tests."""

from core.debug_manager import DebugManager
from core.devtools_manager import DevToolsManager
from core.distributed_memory import DistributedMemory
from core.event_bus import EventBus
from core.fs_sync import FSSync
from core.kernel_summary import KernelSummary
from core.metrics_manager import MetricsManager
from core.profiler_manager import ProfilerManager


def test_devtools_v2_debug_profile_streams_and_inspector(tmp_path):
    """DevTools v2 surfaces should remain simulated and deterministic."""
    events = EventBus()
    memory = DistributedMemory()
    fs_sync = FSSync(tmp_path)
    metrics = MetricsManager(events)
    debug = DebugManager(events, {"memory": memory})
    profiler = ProfilerManager(events)
    devtools = DevToolsManager(events, fs_sync, memory)
    devtools.subscribe_logs("kernel")
    devtools.emit_log("ready", "kernel")
    devtools.fs_write("hello.txt", "world")
    devtools.memory_set("k", "v")
    debug.set_breakpoint("n1", "memory")
    profile = profiler.start_profile("n1", "kernel")
    profiler.collect_profile("n1", "kernel")
    inspector = KernelSummary(memory=memory, fs=fs_sync, metrics=metrics, debug=debug).full()
    assert profile["running"] is True
    assert devtools.fs_read("hello.txt") == "world"
    assert devtools.memory_get("k") == "v"
    assert inspector["debug"]["breakpoints"] == 1
