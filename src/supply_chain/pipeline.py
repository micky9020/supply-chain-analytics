"""End-to-end orchestration: profiling -> cleaning -> KPIs -> scenarios."""
import json
from pathlib import Path

import pandas as pd

from .cleaning import flag_anomalies, normalize, split_valid
from .config import Config
from .financial import scenario_table
from .kpis import add_kpis, headline, summarize


def profile(df: pd.DataFrame) -> dict:
    """Profile the raw file (counts and percentages)."""
    n = len(df)
    dup_rows = int(df.duplicated().sum())
    dup_ids = int(df["pedido_id"].duplicated().sum())
    return {
        "rows": n,
        "missing_by_column": {k: int(v) for k, v in df.isna().sum().items()},
        "exact_duplicate_rows": dup_rows,
        "exact_duplicate_rows_pct": round(100 * dup_rows / n, 2),
        "repeated_order_ids": dup_ids,
        "repeated_order_ids_pct": round(100 * dup_ids / n, 2),
    }


def run(input_csv: str, output_dir: str, cfg: Config | None = None) -> dict:
    cfg = cfg or Config()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(input_csv, dtype=str)          # untouched raw copy
    audit = {"profile": profile(raw)}

    clean, a1 = normalize(raw, cfg)
    clean, a2 = flag_anomalies(clean)
    valid, exceptions, a3 = split_valid(clean, cfg.cutoff)
    audit["cleaning"] = {**a1, **a2, **a3}

    valid = add_kpis(valid, cfg.cutoff)
    summary = headline(valid, cfg.otif_target)
    audit["headline"] = summary

    valid.to_csv(out / "clean_valid.csv", index=False)
    exceptions.to_csv(out / "exceptions.csv", index=False)
    summarize(valid, "mes").to_csv(out / "kpi_monthly.csv", index=False)
    summarize(valid, "almacen").sort_values("otif_pct").to_csv(out / "kpi_by_warehouse.csv", index=False)
    summarize(valid, "transportista").sort_values("otif_pct").to_csv(out / "kpi_by_carrier.csv", index=False)
    scenario_table(summary["total_cost"], cfg.investment, cfg.scenarios).to_csv(
        out / "financial_scenarios.csv", index=False)
    (out / "audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    return audit
