# USER.md

Directive-based user model for this OpenClaw workspace.

## Active

- **2026-09-10** — Operator runs Luna BA cohort studies (xsell / downsell / NTSC as specified per run). Always ask for `lead_segment`, offer date window, and cohort arm definitions; never reuse the previous study’s filters silently.
- **2026-09-10** — Prefer confirm-first workflow: show offer/loan/user counts, then wait for explicit go-ahead before full analysis.
- **2026-09-10** — Present results as a short chat summary with tables first; Excel/CSV under `take_rate_risk/output/` second.
- **2026-09-10** — On Claw, query Redshift only via the platform Redshift tool (emit SQL → tool → CSV → `--data-dir`). Do not use Cred_RS.json.

## Superseded

_(none yet)_
