"""
Luna Wiki risk metrics (risk-metric-ids.md).
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

try:
    import statsmodels.api as sm
except ImportError:  # pragma: no cover
    sm = None

COF_ANNUAL = 0.12
WEEKS_PER_YEAR = 48
COF_PER_DW = COF_ANNUAL / WEEKS_PER_YEAR

WIKI_REF = (
    "https://github.com/credifranco/Luna_BA/blob/main/"
    "luna-wiki/data-dictionary/common/risk-metric-ids.md"
)

KEY_RATE_METRICS = [
    "A2_Pct_Loan_DQ",
    "B2_Pct_DQ_Rem_Principal",
    "B3_Pct_DQ_Rem_Interest",
    "RR3_Pct_Col_Interest",
    "RR4_Pct_Exp_Interest",
    "RR1_Pct_Col_Interest",
    "RR2_Pct_Exp_Interest",
    "DW1_Pct_Cur_Dollarweek",
    "DW2_Pct_Exp_Dollarweek",
    "GACO",
    "ROA_Cur",
    "ROA_Exp",
    "Profit_Cur",
    "Profit_Exp",
    "GM_Cur",
    "GM_Exp",
]

DEV_FACTOR_TO_COMPONENT = {
    "A2": "A2_num_DQ",
    "B2": "B2_DQ_Rem_Principal",
    "B3": "B3_DQ_Rem_Interest",
    "A4": "B1_ESL_Lost_Interest",
    "RR3": "RR3_Col_Interest",
    "RR4": "RR4_Exp_Interest",
    "DW1": "DW1_Cur_Dollarweek",
    "DW2": "DW2_Exp_Dollarweek",
}


def _cap_b2_delta_for_collected_revenue(
    rr3_act: float, b2_delta: float, dw1: float
) -> float:
    """Limit B2 shock so collected-revenue ROA stays non-negative."""
    if dw1 <= 0 or pd.isna(dw1):
        return float(b2_delta)
    max_delta = max(0.0, float(rr3_act) - COF_PER_DW * float(dw1))
    return min(float(b2_delta), max_delta)


def _cap_b2_delta_for_collected_revenue_series(
    rr3_act: pd.Series, b2_delta: pd.Series, dw1: pd.Series
) -> pd.Series:
    max_delta = (rr3_act - COF_PER_DW * dw1).clip(lower=0)
    return np.minimum(b2_delta, max_delta)




def attach_wiki_components(loan_df: pd.DataFrame) -> pd.DataFrame:
    out = loan_df.copy()
    out["cnt_dq"] = out.get("B1_dq_flag", out.get("dq_flag", 0)).fillna(0)
    out["dq_rem_principal"] = out.get(
        "B2Amt_dq_principal",
        out["cnt_dq"] * out["remaining_principal_amt"].fillna(0),
    )
    out["dq_rem_int"] = out["cnt_dq"] * out["remaining_int_amt"].fillna(0)
    out["cum_paid_interest_amt"] = out.get("cum_paid_interest_amt", 0).fillna(0)
    out["cum_paid_lpi_amt"] = out.get("cum_paid_lpi_amt", 0).fillna(0)
    return out


def aggregate_wiki_components(loan_df: pd.DataFrame, segment_cols: list[str]) -> pd.DataFrame:
    work = attach_wiki_components(loan_df)
    agg = {
        "A0_num_Loans": ("loan_id", "count"),
        "A2_num_DQ": ("cnt_dq", "sum"),
        "B0_Principal": ("disbursed_principal_amt", "sum"),
        "B1_ESL_Lost_Interest": ("rev_loss_esl_amt", "sum"),
        "B2_DQ_Rem_Principal": ("dq_rem_principal", "sum"),
        "B3_DQ_Rem_Interest": ("dq_rem_int", "sum"),
        "R0_Exp_Org_Interest": ("expected_original_int_amt", "sum"),
        "R1_Asd_Interest": ("charged_int_amt", "sum"),
        "R2_Asd_LPI": ("charged_lpi_amt", "sum"),
        "R3_Col_Interest": ("cum_paid_interest_amt", "sum"),
        "R4_Col_LPI": ("cum_paid_lpi_amt", "sum"),
        "RR3_Col_Interest": ("cum_rev_amt", "sum"),
        "RR4_Exp_Interest": ("expected_rev_amt", "sum"),
        "DW1_Cur_Dollarweek": ("dollarweeks_capped", "sum"),
        "DW2_Exp_Dollarweek": ("dw4_est_maturity", "sum"),
    }
    if segment_cols:
        return work.groupby(segment_cols, dropna=False).agg(**agg).reset_index()
    totals = {name: work[col].agg(fn) for name, (col, fn) in agg.items()}
    return pd.DataFrame([totals])


def derive_wiki_metrics(comp: pd.DataFrame) -> pd.DataFrame:
    out = comp.copy()
    b0 = out["B0_Principal"].replace(0, np.nan)
    a0 = out["A0_num_Loans"].replace(0, np.nan)
    dw1 = out["DW1_Cur_Dollarweek"].replace(0, np.nan)
    dw2 = out["DW2_Exp_Dollarweek"].replace(0, np.nan)
    d1 = (out["R1_Asd_Interest"] + out["R2_Asd_LPI"]).replace(0, np.nan)

    out["RR1_Col_Interest"] = (
        out["R3_Col_Interest"] + out["R4_Col_LPI"] - out["B2_DQ_Rem_Principal"]
    )
    out["RR2_Exp_Interest"] = (
        out["R0_Exp_Org_Interest"]
        - out["B1_ESL_Lost_Interest"]
        - out["B2_DQ_Rem_Principal"]
        - out["B3_DQ_Rem_Interest"]
    )

    if "A1_num_ESL" in out.columns:
        out["A1_Pct_Loan_ESL"] = out["A1_num_ESL"] / a0
    if "A3_num_Mat" in out.columns:
        out["A3_Pct_Loan_Mat"] = out["A3_num_Mat"] / a0
    out["A4_Pct_ESL_Loss"] = out["B1_ESL_Lost_Interest"] / out["R0_Exp_Org_Interest"].replace(0, np.nan)
    out["A2_Pct_Loan_DQ"] = out["A2_num_DQ"] / a0
    out["B2_Pct_DQ_Rem_Principal"] = out["B2_DQ_Rem_Principal"] / b0
    out["B3_Pct_DQ_Rem_Interest"] = out["B3_DQ_Rem_Interest"] / b0
    out["RR3_Pct_Col_Interest"] = out["RR3_Col_Interest"] / b0
    out["RR4_Pct_Exp_Interest"] = out["RR4_Exp_Interest"] / b0
    out["RR1_Pct_Col_Interest"] = out["RR1_Col_Interest"] / b0
    out["RR2_Pct_Exp_Interest"] = out["RR2_Exp_Interest"] / b0
    out["DW1_Pct_Cur_Dollarweek"] = out["DW1_Cur_Dollarweek"] / b0
    out["DW2_Pct_Exp_Dollarweek"] = out["DW2_Exp_Dollarweek"] / b0

    out["GACO"] = out["B2_DQ_Rem_Principal"] / dw2 * WEEKS_PER_YEAR
    # ROA1 / P1 (Metrics_Definitions.md): cum collected revenue on DW1, not RR1.
    out["ROA_Cur"] = out["RR3_Col_Interest"] / dw1 * WEEKS_PER_YEAR - COF_ANNUAL
    out["ROA_Exp"] = out["RR2_Exp_Interest"] / dw2 * WEEKS_PER_YEAR - COF_ANNUAL
    out["D1_Assessed_Rev"] = out["R1_Asd_Interest"] + out["R2_Asd_LPI"]
    out["Profit_Cur"] = out["RR3_Col_Interest"] - COF_PER_DW * out["DW1_Cur_Dollarweek"]
    out["Profit_Exp"] = out["RR2_Exp_Interest"] - COF_PER_DW * out["DW2_Exp_Dollarweek"]
    out["GM_Cur"] = out["Profit_Cur"] / d1
    out["GM_Exp"] = out["Profit_Exp"] / d1
    return out


def segment_wiki_metrics(loan_df: pd.DataFrame, segment_cols: list[str]) -> pd.DataFrame:
    return derive_wiki_metrics(aggregate_wiki_components(loan_df, segment_cols))


def apply_dev_factors_to_components(
    comp: pd.DataFrame, factors: dict[str, float]
) -> pd.DataFrame:
    out = comp.copy()
    for fac_key, col in DEV_FACTOR_TO_COMPONENT.items():
        fac = factors.get(fac_key)
        if fac is not None and pd.notna(fac):
            out[col] = out[col] * float(fac)
    return out


def row_dev_factors(
    row: pd.Series, portfolio: dict[str, float], seg_factors: pd.DataFrame, segment_cols: list[str]
) -> dict[str, float]:
    if seg_factors.empty:
        return portfolio
    match = seg_factors
    for col in segment_cols:
        match = match[match[col] == row[col]]
    if match.empty:
        return portfolio
    seg = match.iloc[0]
    out = {}
    for fac_key in DEV_FACTOR_TO_COMPONENT:
        col = f"PW24_to_target_{fac_key}"
        val = seg.get(col, portfolio.get(fac_key))
        out[fac_key] = float(val) if pd.notna(val) else portfolio.get(fac_key, np.nan)
    return out


def project_36w_loans_with_factors(
    pw24_36w: pd.DataFrame,
    portfolio_factors: dict[str, float],
    segment_factors: pd.DataFrame,
    segment_cols: list[str],
    source_label: str,
) -> pd.DataFrame:
    rows: list[dict] = []
    comp_base = aggregate_wiki_components(pw24_36w, segment_cols + ["loan_id"])
    for _, loan in pw24_36w.iterrows():
        fac = row_dev_factors(loan, portfolio_factors, segment_factors, segment_cols)
        single = aggregate_wiki_components(
            pw24_36w[pw24_36w["loan_id"] == loan["loan_id"]],
            ["loan_id"],
        )
        projected = apply_dev_factors_to_components(single, fac)
        rec = loan.to_dict()
        rec["cnt_dq"] = projected["A2_num_DQ"].iloc[0]
        rec["dq_flag"] = min(rec["cnt_dq"], 1.0)
        rec["dq_rem_principal"] = projected["B2_DQ_Rem_Principal"].iloc[0]
        rec["B2Amt_dq_principal"] = rec["dq_rem_principal"]
        b3_amt = projected["B3_DQ_Rem_Interest"].iloc[0]
        rec["remaining_int_amt"] = (
            b3_amt / rec["dq_flag"] if rec["dq_flag"] > 0 else 0.0
        )
        rec["rev_loss_esl_amt"] = projected["B1_ESL_Lost_Interest"].iloc[0]
        rec["cum_rev_amt"] = projected["RR3_Col_Interest"].iloc[0]
        rec["expected_rev_amt"] = projected["RR4_Exp_Interest"].iloc[0]
        rec["dollarweeks_capped"] = projected["DW1_Cur_Dollarweek"].iloc[0]
        rec["dw4_est_maturity"] = projected["DW2_Exp_Dollarweek"].iloc[0]
        rec["cum_paid_interest_amt"] = projected["R3_Col_Interest"].iloc[0]
        rec["cum_paid_lpi_amt"] = projected["R4_Col_LPI"].iloc[0]
        rec["projection_source"] = source_label
        rows.append(rec)
    return pd.DataFrame(rows)


def parse_risk_rank(color_grp: str) -> float:
    match = re.search(r"Risk\s+(\d+)", str(color_grp))
    return float(match.group(1)) if match else np.nan


def fit_b2_a2_wls(
    seg_df: pd.DataFrame, weight_col: str = "A0_num_Loans"
) -> object:
    """Loan-weighted WLS: B2/A2 ~ APR + loan_amount1 + risk_rank on PW24 segments."""
    if sm is None:
        raise ImportError("statsmodels is required for B2/A2 WLS model")
    work = seg_df.copy()
    work["risk_rank"] = work["color_grp"].map(parse_risk_rank)
    work["B2_A2_ratio"] = work["B2_Pct_DQ_Rem_Principal"] / work["A2_Pct_Loan_DQ"].replace(0, np.nan)
    valid = work["B2_A2_ratio"].notna() & work["risk_rank"].notna()
    work = work[valid].copy()
    x = sm.add_constant(work[["apr", "loan_amount1", "risk_rank"]].astype(float))
    y = work["B2_A2_ratio"].astype(float)
    w = work[weight_col].astype(float)
    return sm.WLS(y, x, weights=w).fit()


def predict_b2_a2_ratio(
    model: object,
    apr: float,
    loan_amount: float,
    color_grp: str,
) -> float:
    risk_rank = parse_risk_rank(color_grp)
    x = pd.DataFrame(
        [[1.0, float(apr), float(loan_amount), float(risk_rank)]],
        columns=["const", "apr", "loan_amount1", "risk_rank"],
    )
    return float(model.predict(x)[0])


def b2_a2_model_summary(model: object) -> pd.DataFrame:
    rows = []
    for term in model.params.index:
        rows.append(
            {
                "term": term,
                "coef": float(model.params[term]),
                "std_err": float(model.bse[term]),
                "p_value": float(model.pvalues[term]),
            }
        )
    return pd.DataFrame(rows)


def derive_pw24_forecast_from_components(
    comp: pd.Series | dict,
    a2_forecast: float,
    b2_a2_ratio: float,
) -> dict[str, float]:
    row = comp if isinstance(comp, dict) else comp.to_dict()
    b0 = float(row["B0_Principal"])
    dw1 = float(row["DW1_Cur_Dollarweek"])
    dw2 = float(row["DW2_Exp_Dollarweek"])
    b2_fc_rate = a2_forecast * b2_a2_ratio
    b2_fc_amt = b2_fc_rate * b0
    b2_act_amt = float(row["B2_DQ_Rem_Principal"])
    rr3_act = float(row["RR3_Col_Interest"])
    a2_act = float(row["A2_num_DQ"]) / float(row["A0_num_Loans"]) if row["A0_num_Loans"] else np.nan
    if pd.notna(a2_act) and a2_act > 0:
        b2_fc_roa = a2_forecast * (b2_act_amt / a2_act)
    else:
        b2_fc_roa = b2_fc_amt
    b2_delta = _cap_b2_delta_for_collected_revenue(rr3_act, b2_fc_roa - b2_act_amt, dw1)
    rr3_fc = rr3_act - b2_delta
    roa_fc = rr3_fc / dw1 * WEEKS_PER_YEAR - COF_ANNUAL if dw1 > 0 else np.nan
    profit_fc = rr3_fc - COF_PER_DW * dw1
    d1 = float(row.get("D1_Assessed_Rev", row["R1_Asd_Interest"] + row["R2_Asd_LPI"]))
    return {
        "A2_Pct_Loan_DQ_forecast": a2_forecast,
        "B2_A2_ratio_model": b2_a2_ratio,
        "B2_Pct_DQ_Rem_Principal_forecast": b2_fc_rate,
        "GACO_forecast": b2_fc_amt / dw2 * WEEKS_PER_YEAR if dw2 > 0 else np.nan,
        "ROA_Cur_forecast": roa_fc,
        "Profit_Cur_forecast": profit_fc,
        "GM_Cur_forecast": profit_fc / d1 if d1 > 0 else np.nan,
        "RR1_Pct_Col_Interest_forecast": rr3_fc / b0 if b0 > 0 else np.nan,
    }


def apply_a2_model_forecast(
    metrics: pd.DataFrame,
    a2_predicted: pd.Series | None = None,
    b2_a2_ratio: pd.Series | None = None,
) -> pd.DataFrame:
    out = metrics.copy()
    if a2_predicted is None:
        a2_predicted = out.get("A2_Pct_Loan_DQ_predicted")
    out["A2_Pct_Loan_DQ_forecast"] = a2_predicted

    if b2_a2_ratio is None:
        b2_a2_ratio = np.where(
            out["A2_Pct_Loan_DQ"] > 0,
            out["B2_Pct_DQ_Rem_Principal"] / out["A2_Pct_Loan_DQ"],
            np.nan,
        )
    out["B2_A2_ratio_used"] = b2_a2_ratio
    out["B2_Pct_DQ_Rem_Principal_forecast"] = out["A2_Pct_Loan_DQ_forecast"] * b2_a2_ratio

    b2_fc = out["B2_Pct_DQ_Rem_Principal_forecast"] * out["B0_Principal"]
    a2_act = out["A2_Pct_Loan_DQ"].replace(0, np.nan)
    b2_fc_roa = np.where(
        a2_act.notna(),
        out["A2_Pct_Loan_DQ_forecast"] * (out["B2_DQ_Rem_Principal"] / a2_act),
        b2_fc,
    )
    b2_delta = _cap_b2_delta_for_collected_revenue_series(
        out["RR3_Col_Interest"],
        b2_fc_roa - out["B2_DQ_Rem_Principal"],
        out["DW1_Cur_Dollarweek"],
    )
    rr3_fc = out["RR3_Col_Interest"] - b2_delta
    rr2_fc = out["RR2_Exp_Interest"] - b2_delta
    dw1 = out["DW1_Cur_Dollarweek"].replace(0, np.nan)
    dw2 = out["DW2_Exp_Dollarweek"].replace(0, np.nan)

    out["GACO_forecast"] = np.where(
        out["DW2_Exp_Dollarweek"] > 0,
        b2_fc / dw2 * WEEKS_PER_YEAR,
        np.nan,
    )
    out["RR1_Pct_Col_Interest_forecast"] = rr3_fc / out["B0_Principal"].replace(0, np.nan)
    out["RR2_Pct_Exp_Interest_forecast"] = rr2_fc / out["B0_Principal"].replace(0, np.nan)
    out["ROA_Cur_forecast"] = rr3_fc / dw1 * WEEKS_PER_YEAR - COF_ANNUAL
    out["ROA_Exp_forecast"] = rr2_fc / dw2 * WEEKS_PER_YEAR - COF_ANNUAL
    out["Profit_Cur_forecast"] = rr3_fc - COF_PER_DW * out["DW1_Cur_Dollarweek"]
    out["Profit_Exp_forecast"] = rr2_fc - COF_PER_DW * out["DW2_Exp_Dollarweek"]
    d1 = out["D1_Assessed_Rev"].replace(0, np.nan)
    out["GM_Cur_forecast"] = out["Profit_Cur_forecast"] / d1
    out["GM_Exp_forecast"] = out["Profit_Exp_forecast"] / d1
    return out


def _forecast_component_amounts(row: pd.Series) -> dict[str, float]:
    """Reconstruct wiki component amounts from apply_a2_model_forecast row."""
    rr3_fc = float(row["Profit_Cur_forecast"]) + COF_PER_DW * float(row["DW1_Cur_Dollarweek"])
    rr2_fc = float(row["Profit_Exp_forecast"]) + COF_PER_DW * float(row["DW2_Exp_Dollarweek"])
    return {
        "A0_num_Loans": float(row["A0_num_Loans"]),
        "B0_Principal": float(row["B0_Principal"]),
        "A2_num_DQ": float(row["A2_Pct_Loan_DQ_forecast"]) * float(row["A0_num_Loans"]),
        "B1_ESL_Lost_Interest": float(row["B1_ESL_Lost_Interest"]),
        "B2_DQ_Rem_Principal": float(row["B2_Pct_DQ_Rem_Principal_forecast"])
        * float(row["B0_Principal"]),
        "B3_DQ_Rem_Interest": float(row["B3_DQ_Rem_Interest"]),
        "R0_Exp_Org_Interest": float(row["R0_Exp_Org_Interest"]),
        "R1_Asd_Interest": float(row["R1_Asd_Interest"]),
        "R2_Asd_LPI": float(row["R2_Asd_LPI"]),
        "R3_Col_Interest": float(row["R3_Col_Interest"]),
        "R4_Col_LPI": float(row["R4_Col_LPI"]),
        "RR3_Col_Interest": rr3_fc,
        "RR4_Exp_Interest": rr2_fc,
        "DW1_Cur_Dollarweek": float(row["DW1_Cur_Dollarweek"]),
        "DW2_Exp_Dollarweek": float(row["DW2_Exp_Dollarweek"]),
    }


WIKI_COMPONENT_COLS = [
    "A0_num_Loans",
    "B0_Principal",
    "A2_num_DQ",
    "B1_ESL_Lost_Interest",
    "B2_DQ_Rem_Principal",
    "B3_DQ_Rem_Interest",
    "R0_Exp_Org_Interest",
    "R1_Asd_Interest",
    "R2_Asd_LPI",
    "R3_Col_Interest",
    "R4_Col_LPI",
    "RR3_Col_Interest",
    "RR4_Exp_Interest",
    "DW1_Cur_Dollarweek",
    "DW2_Exp_Dollarweek",
]


def project_forecast_components_with_factors(
    comp: dict[str, float],
    factors: dict[str, float],
) -> dict[str, float]:
    """Apply PW24->target dev factors to forecast component amounts."""
    out = dict(comp)
    out["A2_num_DQ"] = comp["A2_num_DQ"] * float(factors.get("A2", 1.0))
    out["B2_DQ_Rem_Principal"] = comp["B2_DQ_Rem_Principal"] * float(factors.get("B2", 1.0))
    out["B3_DQ_Rem_Interest"] = comp["B3_DQ_Rem_Interest"] * float(factors.get("B3", 1.0))
    out["B1_ESL_Lost_Interest"] = comp["B1_ESL_Lost_Interest"] * float(factors.get("A4", 1.0))
    out["RR3_Col_Interest"] = comp["RR3_Col_Interest"] * float(factors.get("RR3", 1.0))
    out["RR4_Exp_Interest"] = comp["RR4_Exp_Interest"] * float(factors.get("RR4", 1.0))
    out["DW1_Cur_Dollarweek"] = comp["DW1_Cur_Dollarweek"] * float(factors.get("DW1", 1.0))
    out["DW2_Exp_Dollarweek"] = comp["DW2_Exp_Dollarweek"] * float(factors.get("DW2", 1.0))
    return out


def project_forecast_segments_to_maturity(
    forecast_metrics: pd.DataFrame,
    portfolio_factors: dict[str, float],
    segment_factors: pd.DataFrame,
    segment_cols: list[str],
    row_factors_fn: object,
) -> pd.DataFrame:
    """
    Maturity forecast = PW24 model-forecast components scaled by PW24->Mat dev factors.

    Uses all PW24-booked segments (not observed maturity rows) so maturity stays
    aligned with the PW24 forecast path.
    """
    rows: list[dict] = []
    for _, row in forecast_metrics.iterrows():
        fac = row_factors_fn(row, portfolio_factors, segment_factors)
        comp = project_forecast_components_with_factors(
            _forecast_component_amounts(row),
            fac,
        )
        rec = {col: row[col] for col in segment_cols}
        rec.update(comp)
        rows.append(rec)
    comp_df = pd.DataFrame(rows)
    derived = derive_wiki_metrics(comp_df)
    metric_cols = [c for c in derived.columns if c not in segment_cols]
    return pd.concat(
        [comp_df[segment_cols].reset_index(drop=True), derived[metric_cols].reset_index(drop=True)],
        axis=1,
    )
