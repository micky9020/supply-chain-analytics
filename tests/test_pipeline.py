import math

import pandas as pd

from supply_chain.cleaning import flag_anomalies, normalize, split_valid
from supply_chain.config import Config
from supply_chain.financial import otif_uplift, scenario_table
from supply_chain.kpis import add_kpis

CUTOFF = "2026-06-30"


def make(rows):
    cols = ["pedido_id", "fecha_pedido", "fecha_prometida", "fecha_entrega", "almacen",
            "transportista", "unidades_pedidas", "unidades_entregadas", "costo_transporte", "estado"]
    return pd.DataFrame(rows, columns=cols, dtype=str)


def prepare(rows):
    clean, _ = normalize(make(rows), Config())
    clean, _ = flag_anomalies(clean)
    return split_valid(clean, CUTOFF)


def test_alias_and_whitespace_are_standardized():
    df = make([["A1", "01/03/2026", "05/03/2026", "05/03/2026", " lima sur ", "t. andino",
                "10", "10", "50", "entreg."]])
    clean, _ = normalize(df, Config())
    assert clean.loc[0, "almacen"] == "LIMA SUR"
    assert clean.loc[0, "transportista"] == "TRANSPORTES ANDINO"
    assert clean.loc[0, "estado"] == "ENTREGADO"


def test_exact_duplicates_removed_but_conflicting_ids_flagged():
    row = ["A1", "01/03/2026", "05/03/2026", "05/03/2026", "X", "Y", "10", "10", "50", "ENTREGADO"]
    conflict = row.copy()
    conflict[8] = "99"
    clean, _ = normalize(make([row, row, conflict]), Config())
    clean, audit = flag_anomalies(clean)
    assert audit["exact_duplicates_removed"] == 1
    assert clean["error_id_duplicado"].all() and len(clean) == 2


def test_open_not_due_excluded_and_open_overdue_fails():
    valid, _, audit = prepare([
        ["NOT_DUE", "20/06/2026", "05/07/2026", None, "X", "Y", "10", None, "50", "PENDIENTE"],
        ["OVERDUE", "01/06/2026", "10/06/2026", None, "X", "Y", "10", None, "50", "PENDIENTE"],
        ["OK", "01/06/2026", "10/06/2026", "09/06/2026", "X", "Y", "10", "10", "50", "ENTREGADO"],
    ])
    assert audit["excluded_not_yet_due"] == 1
    out = add_kpis(valid, CUTOFF).set_index("pedido_id")
    assert not out.loc["OVERDUE", "otif"] and out.loc["OK", "otif"]
    assert out.loc["OVERDUE", "dias_retraso"] == 20           # 10/06 -> 30/06


def test_late_or_incomplete_is_not_otif_and_month_uses_promised_date():
    valid, _, _ = prepare([
        ["LATE", "28/01/2026", "02/02/2026", "04/02/2026", "X", "Y", "10", "10", "50", "ENTREGADO"],
        ["SHORT", "01/03/2026", "05/03/2026", "05/03/2026", "X", "Y", "10", "8", "50", "ENTREGADO"],
    ])
    out = add_kpis(valid, CUTOFF).set_index("pedido_id")
    assert not out["otif"].any()
    assert out.loc["LATE", "mes"] == "2026-02"                # promised month, not the order month


def test_data_errors_go_to_exceptions():
    valid, exc, _ = prepare([
        ["NEG", "01/03/2026", "05/03/2026", "05/03/2026", "X", "Y", "10", "10", "-5", "ENTREGADO"],
        ["EXCESS", "01/03/2026", "05/03/2026", "05/03/2026", "X", "Y", "10", "12", "5", "ENTREGADO"],
        ["BADDATE", "10/03/2026", "05/03/2026", "05/03/2026", "X", "Y", "10", "10", "5", "ENTREGADO"],
    ])
    assert valid.empty and set(exc["pedido_id"]) == {"NEG", "EXCESS", "BADDATE"}


def test_financial_scenarios_match_case_study():
    t = scenario_table(2_400_000, 30_000, Config().scenarios).set_index("scenario")
    assert t.loc["Base case", "gross_savings"] == 120_000
    assert t.loc["Base case", "net_benefit"] == 90_000
    assert round(t.loc["Conservative", "roi_pct"]) == 140
    assert round(t.loc["Upside", "roi_pct"]) == 540
    assert math.isnan(scenario_table(1000, 0, {"x": 0.1})["roi_pct"].iloc[0])


def test_otif_uplift_matches_case_study():
    r = otif_uplift(50_000, 0.88, 0.95)
    assert (r["otif_now"], r["otif_target"], r["additional"]) == (44_000, 47_500, 3_500)
    assert r["relative_growth_pct"] == 7.95
