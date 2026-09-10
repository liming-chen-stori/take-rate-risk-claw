---
name: take-rate-risk-cohorts
description: >-
  Runs multi-cohort Luna take-rate and risk analysis with a confirm-first gate.
  Compares offer mix (date, offer times 1/2/3/4+, risk band), take rate by offer
  times and risk band, loan-term similarity (limit, tenor, payment frequency),
  and risk metrics (A0, A2, B2, RR1, RR2, GACO, ROA, GM) by payweek when A0 is
  large enough. Use when the user asks for take rate, risk checker, cohort
  compare, BAU vs test, study vs control, offer balance, or Luna offer
  performance across arms (xsell first/subsequent, downsell, new-to-stori, etc.).
---

# Take-rate & risk cohort compare

## Engine location (do not reinvent SQL)

Package root: this folder (run commands from here).

```
take_rate_risk/
  configs/          # one YAML per run
  scripts/cohort_compare.py
  scripts/wiki_metrics.py
  output/<run_name>/
```

Copy `take_rate_risk/configs/example_two_cohorts.yaml` → `take_rate_risk/configs/<run_name>.yaml` and edit.

## Credentials (each user)

Teammates must provide **their own** Redshift login in `Cred_RS.json` (gitignored).

1. Copy `Cred_RS.example.json` → `Cred_RS.json`
2. Fill `username`, `password`, `host`, `port`, `database`
3. Or set env `CRED_RS_PATH` to their credentials file

Never commit `Cred_RS.json`. If missing, stop and ask the user to create it from the example.

## Hard rules

1. **Never skip the confirm gate.** Define cohorts → write YAML → run `--phase confirm` → show counts → wait for explicit user OK → only then `--phase all`.
2. **Do not rewrite metric SQL each run.** Change only YAML cohort knobs (`shared_where`, `cohorts[].where` / `offer_sql`, dates, `payweeks`, `min_a0`).
3. Present results **chat summary first**, then canvas if useful, then Excel under `take_rate_risk/output/<run_name>/`.

## Step 1 — Ask how to define cohorts

Ask (adapt to context; do not dump all if user already specified):

- What are the **cohorts** to compare? (names + how each is defined)
- Common patterns: test vs study, BAU vs test arm, tenor set, freq arm, date windows, `test_description` / `policy_dcsn_note` / SUPER offer_conditions
- Shared filters? Always ask case by case — do **not** reuse prior-run values:
  - `lead_segment` (xsell first/subsequent, downsell, new-to-stori, …) — never default to `xs-first-loan`
  - `offer_creation_dt` window — different every study
  - `test_description` / other arm keys — only in `shared_where` if identical for all cohorts; otherwise per-cohort `where`
- Booking window (default 60d), payweeks (default 4…24), `min_a0` (default 30)
- Offer-times scope: `within_cohort` (default) vs `across_all`

Then write the YAML under `take_rate_risk/configs/`. Prefer `shared_where` + per-cohort `where`. Use `offer_sql` only when needed.

## Step 2 — Confirm before proceeding

From this folder:

```powershell
python take_rate_risk\scripts\cohort_compare.py `
  --config take_rate_risk\configs\<run_name>.yaml `
  --phase confirm
```

Show the user:

- Restated cohort definitions (shared + each arm)
- Table: cohort | offers | loans_60d | users

**Stop.** Ask: “Proceed with offer balance, take rate, loan terms, and risk?”

Do not run `--phase all` until the user confirms.

## Step 3 — Full analysis

```powershell
python take_rate_risk\scripts\cohort_compare.py `
  --config take_rate_risk\configs\<run_name>.yaml `
  --phase all
```

### 2) Offer comparison (balance check)

- Counts by cohort; by offer date; by offer times (1/2/3/4+); by risk band
- Call out material mix skews before interpreting take rate / risk

### 3) Take rate

Overall + by offer times + by risk band (loans within `booking_window_days` / offers).

### 4) Loan terms (booked only)

Avg limit, % max/min limit, avg tenor, % min/max tenor, weekly/biweekly/monthly.

### 5) Risk

A0, A2, B2, RR1, RR2, GACO, ROA, GM by payweek only when `A0 >= min_a0`.

## Anti-patterns

- Rewriting metric SQL per test when YAML suffices
- Skipping offer-mix balance
- Showing thin A0 payweeks
- Fabricating numbers on query failure
- Committing or pasting `Cred_RS.json` secrets
