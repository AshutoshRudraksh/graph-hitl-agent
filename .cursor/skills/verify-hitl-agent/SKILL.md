---
name: verify-hitl-agent
description: >-
  Drive the graph-hitl-agent CLI (main.py) in an isolated PTY to prove the
  balance lookup, transfer approval, and transfer rejection. Use when verifying
  the HITL agent terminal session, the approval prompt, or approve/reject behavior.
---

# Verify the HITL agent CLI

The user-facing surface is the short-lived CLI `main.py`. It prints a balance, pauses on a transfer approval prompt, and applies `y` or `n`. There is no web UI and no HTTP server. Pytest covers the library; it is not this harness.

Each drive starts its own `main.py` process. Checkpoint state and the transfer ledger live in that process, so two drives can run at the same time. Do not type into a `main.py` the user already started.

## Launch

From the repo root, confirm the CLI can be imported. This process exits on its own; there is no server to leave running.

```bash
/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.venv/bin/python -c "import hitl_agent, main; print('HITL agent import ok')"
```

Ready when stdout is `HITL agent import ok` and the exit code is 0. A drive is ready later, when its transcript contains `Approve this transfer? (y/n):`.

## Doctor

Run this before every drive. It does not start `main.py`.

```bash
/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/bin/verify-hitl doctor
```

Worth driving only when stdout contains all of:

```text
doctor: ok
python: /Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.venv/bin/python
version: 0.1.0
prompt: Approve this transfer? (y/n):
repo: /Users/stacbot/Downloads/graph-agent/graph-hitl-agent
```

Exit code `1` means the venv, the import, or the prompt string is missing. Stop. Do not point the harness at another Python.

## Drive

The helper launches `main.py` in a new PTY, waits for `Approve this transfer? (y/n):`, sends one answer, and records the transcript. The CLI itself always sends `Please check my balance` and then `Transfer $500 from acc_A to acc_B` for user `usr_9876` on thread `local-cli`. The human's only keystroke is `y` or `n`.

```bash
/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/bin/verify-hitl drive check-balance
/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/bin/verify-hitl drive approve-transfer
/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/bin/verify-hitl drive reject-transfer
```

A drive is proven only when it prints `ok: true`, `exit_code: 0`, and the transcript path. Read `features/README.md` and the feature file before choosing a command. One green drive does not cover the other entries.

## Evidence

Transcripts and `result.json` files are written under:

`/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/artifacts/<feature>/<run-id>/`

Proof standards:

- Drive `main.py` through the helper. Do not call `AgentService`, graph nodes, or pytest as the proof.
- The transcript must show the prompt and the lines after the answer, not only the final status line.
- The transfer has no database row. The tool message in the transcript is the side effect. For approval, the idempotency key printed in the interrupt before the prompt must be the only key in the transcript, and the following tool message must report `SUCCESS` for `acc_A` to `acc_B` at `500.0`.
- The balance and transfer tools are in-process mocks. That is the app's real boundary. Do not add another mock, and do not require a network call or a Postgres write; this CLI uses neither.
- `result.json` is parsed from the transcript. It is not a substitute for reading the transcript.

## Cleanup

```bash
/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/bin/verify-hitl cleanup
```

This terminates only PIDs the helper recorded whose command line is still this repo's `main.py`, then deletes `.cursor/skills/verify-hitl-agent/.scratch/`. It does not delete `artifacts/`. After cleanup, the transcript path from the drive must still exist.

## Helpers

`/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/bin/verify-hitl`

- `verify-hitl doctor` — read-only readiness check. Exit 0 or 1.
- `verify-hitl drive check-balance` — PTY session that answers `n`. Proves the balance printed before the prompt and that no transfer succeeded.
- `verify-hitl drive approve-transfer` — PTY session that answers `y`. Proves the staged transfer and the executed transfer are the same.
- `verify-hitl drive reject-transfer` — PTY session that answers `n`. Proves the staged transfer was cancelled.
- `verify-hitl cleanup` — stop recorded CLI processes and remove scratch. Leaves artifacts.

The helper sets `PYTHONUNBUFFERED=1` for the child so the approval prompt is visible before it sends the answer.
