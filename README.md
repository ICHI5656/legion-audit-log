# Legion Audit Log

This public repository provides sanitized, append-only progress summaries for
Legion OS governance. It lets the owner and the command-room reviewer inspect
decisions and milestones without access to the private implementation
repository.

## Public Content Boundary

Only the following information belongs here:

- progress summaries;
- owner decisions and review outcomes;
- non-sensitive rationale;
- content digests;
- `escalation_class` values.

Secrets, infrastructure coordinates, personal or customer information,
business source data, private source code, credentials, and internal
connection details are prohibited. See
[SANITIZATION_POLICY.md](SANITIZATION_POLICY.md).

## Layout

- `audit-log/YYYY-MM-DD.md`: one sanitized daily audit log;
- `scripts/scan-public-content.py`: fail-closed public-content scanner;
- `.githooks/pre-push`: local pre-push enforcement.

## Required Local Setup

Install the repository-owned hook once after cloning:

```bash
./scripts/install-hooks.sh
```

Before committing or pushing, run:

```bash
python3 scripts/scan-public-content.py --all
```

The pre-push hook runs the same scan. A finding or an unreadable, binary, or
oversized tracked file blocks the push.
