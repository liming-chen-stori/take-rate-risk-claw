# TOOLS.md

Local conventions for this workspace. Guidance only — does not enable/disable tools.

## Working directory

Always treat the repo root as cwd.

## Redshift (Claw platform tool)

**Primary data path on Claw:** use the platform **Redshift tool** (execute-query / export).  
**Do not** use `Cred_RS.json` or ask for warehouse passwords.

### Emit SQL (Python, no DB)

```powershell
python take_rate_risk\scripts\cohort_compare.py `
  --config take_rate_risk\configs\<run_name>.yaml `
  --phase confirm `
  --emit-sql
```

SQL → `take_rate_risk/output/<run_name>/sql/`

### Run + export

1. Execute each `.sql` with the platform Redshift tool.
2. Export CSVs into `take_rate_risk/output/<run_name>/raw/` as:
   - `confirm.csv`
   - `offers_detail.csv`
   - `risk_raw.csv`

### Aggregate (Python, no DB)

```powershell
python take_rate_risk\scripts\cohort_compare.py `
  --config take_rate_risk\configs\<run_name>.yaml `
  --phase all `
  --data-dir take_rate_risk\output\<run_name>\raw
```

Phases: `confirm` | `offers` | `take_rate` | `loan_terms` | `risk` | `all`

Supporting module: `take_rate_risk/scripts/wiki_metrics.py` (imported by the engine).

## Config files

- Template: `take_rate_risk/configs/example_two_cohorts.yaml`
- Example study: `take_rate_risk/configs/202607_policy_tightening.yaml`
- New runs: copy template → `take_rate_risk/configs/<run_name>.yaml`

## Credentials

- **Claw:** none — Redshift tool handles auth.
- **Local optional only:** `--use-creds` + `Cred_RS.example.json` → `Cred_RS.json` (gitignored). Never on Claw.

## Outputs

`take_rate_risk/output/<run_name>/` (gitignored). Summarize in chat before pointing to files.

## Skill trigger

When the user asks for take rate, risk checker, cohort compare, BAU vs test, study vs control, or offer balance — load `skills/take-rate-risk-cohorts/SKILL.md` and follow it.
