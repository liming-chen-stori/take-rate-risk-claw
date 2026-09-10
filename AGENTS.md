# AGENTS.md

## Role

OpenClaw workspace for Luna multi-cohort take-rate and risk analysis.

## Primary skill

Use **`take-rate-risk-cohorts`** for any cohort compare / take-rate / risk-checker request.

Skill path: `skills/take-rate-risk-cohorts/SKILL.md`

## Workspace layout

```
./
  AGENTS.md IDENTITY.md TOOLS.md USER.md SOUL.md
  skills/take-rate-risk-cohorts/SKILL.md
  take_rate_risk/
    configs/          # one YAML per run
    scripts/cohort_compare.py
    scripts/wiki_metrics.py
    output/<run_name>/
  Cred_RS.example.json
  requirements.txt
```

Package root = this folder. Run all Python from here.

## Operating priorities

1. Follow `skills/take-rate-risk-cohorts/SKILL.md` exactly.
2. Confirm gate before any `--phase all` (or offers / take_rate / loan_terms / risk).
3. Chat summary first; files under `take_rate_risk/output/<run_name>/` second.
4. Prefer editing YAML over changing Python.

## Memory

- Session decisions (cohort names, date windows, `lead_segment`) belong in the chat reply and the run YAML — not in secrets files.
- Do not store passwords or Redshift credentials in memory files.

## Tools

See `TOOLS.md` for local tool conventions.
