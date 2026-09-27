# HITL agent verification map

This directory is the maintained source for verifying the user-facing behavior of the graph-hitl-agent CLI. Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Repo root: `/Users/stacbot/Downloads/graph-agent/graph-hitl-agent`.
- Interpreter: `/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.venv/bin/python`.
- Run `verify-hitl doctor` and require `doctor: ok`, version `0.1.0`, and prompt `Approve this transfer? (y/n):`.
- Start each drive with `verify-hitl drive <feature>`. Each command starts a new PTY and a new `main.py`.
- Never type into a `main.py` the user already has open. In-memory checkpoints die with the process, and a second writer on that terminal corrupts the session.
- Two helper drives may run at the same time. They do not share checkpoint state.
- Leave files under `artifacts/` in place. Cleanup removes `.scratch/` only.

## Driving conventions

- The only user keystroke is `y` or `n` at `Approve this transfer? (y/n):`.
- The CLI always asks, in order, `Please check my balance` and `Transfer $500 from acc_A to acc_B` for user `usr_9876`.
- Treat helper commands as literal. Do not pass extra arguments.
- Capture the transcript path the command prints. Assertions read that transcript and its `result.json`.
- Do not report a skipped feature as verified because another feature's transcript contains some of the same lines.

## Proof and skip reporting

- Prove the prompt and the lines after the answer, not only `paused=False`.
- Approval proof compares the interrupt payload before the prompt with the tool message after `y`.
- Rejection and balance proofs must show no `"status": "SUCCESS"` anywhere in the transcript.
- Record the feature id and the transcript path with the proof.
- Report an unreachable path with the command that failed and the unmet doctor line.
- There is no second screen after the process exits. The transcript is the session record.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with verify-hitl` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

## Features

- [Check balance](./check-balance.md) covers the balance printed before the approval prompt.
- [Approve transfer](./approve-transfer.md) covers accepting the staged `$500` transfer from `acc_A` to `acc_B`.
- [Reject transfer](./reject-transfer.md) covers cancelling that transfer from the same prompt.
