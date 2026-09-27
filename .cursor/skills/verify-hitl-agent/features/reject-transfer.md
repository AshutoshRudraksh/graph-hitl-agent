# Reject transfer

Reject transfer shows the same staged `$500` transfer as approval, then cancels it when the user types `n`. No funds move.

## Sub-features

- `reject-pause` shows the staged transfer and the approval prompt.
- `reject-cancel` reports the transfer cancelled after `n`.
- `reject-no-success` does not print a successful tool result.

## How to get to it (user POV)

- Run `python main.py` with the project virtualenv.
- At `Approve this transfer? (y/n):`, type `n` and press Enter.

## Driving it with verify-hitl

Preconditions:

- `verify-hitl doctor` prints `doctor: ok` and `version: 0.1.0`.
- No `main.py` for this repo is already running in the terminal you will read.

- **Pause for approval.** Run `/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/bin/verify-hitl drive reject-transfer`. Before `Approve this transfer? (y/n):`, the transcript contains `HUMAN_APPROVAL_REQUIRED`, `acc_A`, and `acc_B`.
- **Reject.** The helper types `n`. The command prints `ok: true` and `exit_code: 0`.
- **Confirm cancellation.** The lines after the prompt contain `cancelled`. The transcript contains no `"status": "SUCCESS"`.
- **Proof.** `result.json` has `interrupt_seen` true and `ok` true.

## Gotchas

- `check-balance` also answers `n`. Do not treat a balance transcript as proof of this feature. Run `drive reject-transfer` and keep that transcript.
- The cancel line is printed only after `n`. A transcript that stops at the prompt does not prove rejection.
- There is no persisted ledger to query afterward. The absence of `SUCCESS` has to be in this transcript.
