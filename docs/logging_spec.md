# ANA MAX Logging Specification

ANA MAX OS v2 logging is structured and trace-oriented.

The logging subsystem provides:
- a dedicated structured logger in `ana/core/logging`
- trace identifiers for every orchestrator request
- event bus publication for `log.entry`
- formatted JSON log payloads for external consumers
- audit metadata attached to sandbox execution results

Logging does not replace the event bus. Instead, it augments observability by making runtime decisions explicit and queryable.
