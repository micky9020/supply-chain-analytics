"""Savings scenarios. These are assumptions, not a forecast."""
import pandas as pd


def scenario_table(baseline_cost: float, investment: float, rates: dict) -> pd.DataFrame:
    """Gross savings = baseline cost x rate; net benefit = gross - investment; ROI = net / investment."""
    rows = []
    for name, rate in rates.items():
        gross = baseline_cost * rate
        net = gross - investment
        roi = net / investment * 100 if investment else float("nan")  # ROI is undefined without investment
        rows.append({"scenario": name, "reduction_pct": rate * 100, "gross_savings": gross,
                     "net_benefit": net, "roi_pct": roi})
    return pd.DataFrame(rows)


def otif_uplift(orders: int, current: float, target: float) -> dict:
    """Additional OTIF orders when moving from `current` to `target` (proportions 0-1)."""
    now, goal = round(orders * current), round(orders * target)
    return {"otif_now": now, "otif_target": goal, "additional": goal - now,
            "relative_growth_pct": round((goal - now) / now * 100, 2) if now else None}
