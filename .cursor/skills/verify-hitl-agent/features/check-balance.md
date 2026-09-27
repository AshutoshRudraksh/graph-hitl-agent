# Check balance

Check balance shows the signed-in user's account balance in the terminal before the CLI asks whether to approve a transfer.

## Sub-features

- `balance-open` runs the CLI and shows the balance before any approval answer.
- `balance-identity` shows the balance for user `usr_9876`.
- `balance-no-transfer` leaves the session without a successful transfer when the user declines.

## How to get to it (user POV)

- Run `python main.py` with the project virtualenv and read the terminal until the approval prompt.

## Driving it with verify-hitl

Preconditions:

- `verify-hitl doctor` prints `doctor: ok` and `version: 0.1.0`.
- No `main.py` for this repo is already running in the terminal you will read.

- **Open the session.** Run the CLI and read the balance before answering. Run `/Users/stacbot/Downloads/graph-agent/graph-hitl-agent/.cursor/skills/verify-hitl-agent/bin/verify-hitl drive check-balance`. The command prints `ok: true` and `exit_code: 0`. The transcript contains `balance_usd` and `usr_9876` before `Approve this transfer? (y/n):`.
- **Decline so the process can exit.** The helper answers `n` after the balance is on screen. In that same transcript, the lines after the prompt contain `cancelled` and the file contains no `"status": "SUCCESS"`.
- **Proof.** Read `result.json` next to the transcript. `balance_seen` is true and `ok` is true.

## Gotchas

- The user cannot type a different user id. This entry point always looks up `usr_9876`.
- Answering `y` executes the transfer. That is a different feature. This drive must answer `n`.
- The balance is an in-memory mock. Proof is the tool line in the transcript, not a database query.
- The process exits after the answer. Starting `main.py` again starts a new session; it does not reopen this balance.
