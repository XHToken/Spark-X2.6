# Spark-X2.6 issue triage

Local rules-based issue classification and GitHub Projects synchronization. All GitHub reads and writes go through the locally authenticated `gh` CLI. Writes require the expected `FenjuFu` account. No GitHub connector or Actions bot is used.

## Run

Requires Python 3.11+, GitHub CLI, and `gh auth login` with repository access. Project creation/sync also needs `gh auth refresh -s project` and permission to manage XHToken Projects.

```powershell
python -m unittest -v
python triage.py                # preview only, no GitHub writes
python setup_project.py        # create/reconcile the dedicated project
python triage.py --apply       # create missing labels, classify, add/sync cards
```

`setup_project.py` finds the dedicated project by its exact title before creating it. It saves field/option IDs in `project.json`. It preserves existing field values when extending status options. It configures seven views: Delivery, Inbox, Priority, Agent ready, Blocked, Community, All issues. The board uses GitHub's default Status grouping; grouping and sorting can be adjusted in the UI.

## Daily workflow

- `Triage`: new feedback awaits confirmation. Set an assignee and move to `Ready` when scheduled.
- `In progress`: somebody is actually working on it. `Blocked`: external dependency. `In review`: waiting for review/verification.
- Closing an issue moves its existing card to `Done`. The automation never closes an issue. Reopening preserves the current card status; a maintainer moves it back to `Triage` or `Ready`.
- Five label dimensions: `area/*`, `priority/*`, `effort/*`, `risk/*`, `triage/*`. Labels are the source of truth for matching Project fields; edit the label to change classification.
- Existing labels in each dimension are preserved. To reclassify one dimension, remove its labels and run again. Conflicting labels in one dimension require manual resolution.
- `triage-manual` pauses both classification and project sync for that issue. Other existing labels, including bounty/reward/campaign labels, are untouched.
- `priority/p0` is manual only. `unknown` means unassessed. `triage/agent-ready` is a candidate for low-risk assistance, not an authorization to execute or merge code.
- No comments, assignments, deletions or merges are performed. Status changes made by maintainers are preserved while the issue is open.

Rules currently use the title and body, not comment history. They are conservative initial routing, not a diagnosis or implementation estimate. Check stale issues during weekly triage; age alone does not make an issue P0.

## Windows schedule

Run `powershell -NoProfile -File .\install-task.ps1` once after a successful manual run. The task `Spark-X2.6 Issue Triage` runs at login and every 30 minutes while the user is logged in and the machine has network access. It uses the user's keyring-backed `gh` login, with no copied token and no elevated Windows privileges. It does not fetch or execute remote code. Keep this deployment folder stable.

`runtime.json` contains only local executable paths. `state/latest.json` contains the latest assessment report, `state/last-run.log` the latest execution output, and `state/run-status.json` the completion status. Parallel runs are prevented by an exclusive lock. Check task status with:

```powershell
Get-ScheduledTaskInfo -TaskName 'Spark-X2.6 Issue Triage'
Disable-ScheduledTask -TaskName 'Spark-X2.6 Issue Triage' # pause
Enable-ScheduledTask -TaskName 'Spark-X2.6 Issue Triage'  # resume
```

## Optional Spark / compatible model endpoint

Rules work without a model or paid subscription. To enable semantic classification for missing label dimensions, configure these environment variables for the process that runs triage:

- `TRIAGE_MODEL_URL`: full chat completions endpoint, e.g. `http://127.0.0.1:30000/v1/chat/completions` for a locally served Spark model.
- `TRIAGE_MODEL`: the server's actual served model name, e.g. `spark2.6` when configured that way for Spark-X2.6-4B.
- `TRIAGE_MODEL_API_KEY`: optional endpoint credential. Store it securely; do not commit it.

Model mode sends the issue title and up to 12,000 body characters to the configured endpoint. It never sends GitHub credentials. HTTPS is required except for loopback servers; redirects are rejected. The model has no tools. Responses must match the allowlisted categories with confidence >= 0.85; malformed, low-confidence, timed-out or unavailable responses fall back to rules. Existing human labels remain authoritative. This is an inference adapter, not a model server installer, and the model integration must be validated against the chosen service before production use.

## Other agents

GitHub Agentic Workflows supports Copilot, Codex and Claude engines. Those are alternatives when deeper repository analysis is useful. Cloud inference credentials and GitHub write identity are separate concerns. This local implementation intentionally retains the user's requested local `gh` write identity. No agent subscription, connector, cloud workflow or model service is enabled by these scripts.

References: [GitHub engines](https://github.github.io/gh-aw/introduction/how-they-work/), [GitHub authentication](https://github.github.io/gh-aw/reference/auth/), [Codex automation authentication](https://learn.chatgpt.com/docs/non-interactive-mode#use-api-key-auth).
