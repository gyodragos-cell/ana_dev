# ANA MAX v28 Dev Snapshot

## Summary

The v28 dev kernel turns the AI OS layer from scaffolding into a compact working local simulation. Nodes, remote calls, distributed memory, events, semantic files, permissions, services, and security checks now have testable behavior.

## Known Issues

- Remote execution is still in-process by default.
- Dashboard UI is intentionally minimal.
- Distributed memory is in-memory only.
- Safe-mode policy is enforced by convention and tests, not a persistent daemon.

## Next Steps

- Add long-running stress runs.
- Add audit trail integration for distributed operations.
- Add dashboard HTTP serving command.
- Decide which docs are safe for public sync.
