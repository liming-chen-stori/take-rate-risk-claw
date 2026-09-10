# TOOLS.md

Local conventions for this workspace. Guidance only — does not enable/disable tools.

## Working directory

Always treat the repo root as cwd:

```
take-rate-risk-claw/
```

## Python engine

```powershell
pip install -r requirements.txt

python take_rate_risk\scripts\cohort_compare.py `
  --config take_rate_risk\configs\<run_name>.yaml `
  --phase confirm

python take_rate_risk\scripts\cohort_compare.py `
  --config take_rate_risk\configs\<run_name>.yaml `
  --phase all
```

Phases: `confirm` | `offers` | `take_rate` | `loan_terms` | `risk` | `all`

Supporting module: `take_rate_risk/scripts/wiki_metrics.py` (imported by the engine — do not call alone unless debugging).

## Config files

- Template: `take_rate_risk/configs/example_two_cohorts.yaml`
- Example study: `take_rate_risk/configs/202607_policy_tightening.yaml`
- New runs: copy template → `take_rate_risk/configs/<run_name>.yaml`

## Credentials

- Template only in git: `Cred_RS.example.json`
- Operator creates local `Cred_RS.json` (gitignored) or sets `CRED_RS_PATH`
- Never print password fields

## Outputs

Write under `take_rate_risk/output/<run_name>/` (gitignored). Summarize in chat before pointing to files.

## Skill trigger

When the user asks for take rate, risk checker, cohort compare, BAU vs test, study vs control, or offer balance — load `skills/take-rate-risk-cohorts/SKILL.md` and follow it.
