# Approve transfer

Approve transfer pauses on a `$500` transfer from `acc_A` to `acc_B`, then moves the funds only after the user types `y`.

## Sub-features

- `approve-pause` shows the approval prompt and the staged transfer before any keystroke.
- `approve-execute` completes that same transfer after `y`.
- `approve-same-key` uses one idempotency key in both the prompt payload and the tool result.

## How to get to it (user POV)

- Run `python main.py` with the project virtualenv.
- At `Approve this transfer? (y/n):`, type `y` and press Enter.

## Driving it with verify-hitl

Preconditions:

- `verify-hitl doctor` prints `doctor: ok` and `version: 0.1.0`.
- No `main.py` for this repo is already running in the terminal you will read.

- **Pause for approval.** Run the CLI through the harness. Run `/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/bin/verify-hitl drive approve-transfer`. The transcript contains `paused=True`, `HUMAN_APPROVAL_REQUIRED`, and `execute_funds_transfer` before `Approve this transfer? (y/n):`.
- **Approve.** The helper types `y` at that prompt. The command prints `ok: true` and `exit_code: 0`.
- **Confirm the transfer.** In the lines after the prompt, the transcript contains `"status": "SUCCESS"`, `"source": "acc_A"`, `"destination": "acc_B"`, `"amount_usd": 500.0`, and `successfully executed`.
- **Confirm the same action.** `result.json` field `idempotency_keys` contains the same key twice and no other key. That key is in the interrupt before the prompt and in the tool message after `y`.

## Gotchas

- The staged accounts and amount come from the CLI's fixed sentence `Transfer $500 from acc_A to acc_B`. A different sentence is not available at this entry point.
- Typing `y` into a `main.py` you did not start mixes with the user's session. Use the helper.
- Memory for the thread disappears when the process exits. Do not launch a second `main.py` to look up the transaction.
- `paused=False` at the end is not enough. The tool message after `y` has to match the interrupt shown before the prompt.
