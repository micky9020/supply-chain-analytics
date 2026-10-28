"""Standardization, anomaly detection and separation of valid records from exceptions.

Principle: evidence is never deleted silently. Every rule leaves a count in the audit
and flagged records go to an exceptions table.
"""
import pandas as pd

from .config import Config

TEXT_COLS = ["pedido_id", "almacen", "transportista", "estado"]
DATE_COLS = ["fecha_pedido", "fecha_prometida", "fecha_entrega"]
NUM_COLS = ["unidades_pedidas", "unidades_entregadas", "costo_transporte"]
ERROR_COLS = ["error_id_duplicado", "error_cantidad", "error_costo", "error_fechas"]


def normalize(df: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, dict]:
    """Normalize column names, text, dates and numbers. Returns (df, audit)."""
    clean = df.copy()
    clean.columns = clean.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    audit: dict = {}

    for col in TEXT_COLS:
        clean[col] = clean[col].astype("string").str.strip().str.upper()
    clean["transportista"] = clean["transportista"].replace(cfg.carrier_map)
    clean["estado"] = clean["estado"].replace(cfg.status_map)

    for col in DATE_COLS:
        parsed = pd.to_datetime(clean[col], errors="coerce", format=cfg.date_format)
        audit[f"invalid_{col}"] = int((parsed.isna() & clean[col].notna()).sum())
        clean[col] = parsed

    for col in NUM_COLS:
        parsed = pd.to_numeric(clean[col], errors="coerce")
        audit[f"non_numeric_{col}"] = int((parsed.isna() & clean[col].notna()).sum())
        clean[col] = parsed

    return clean, audit


def flag_anomalies(clean: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Remove exact duplicates only; flag every other anomaly instead of deleting it."""
    n_before = len(clean)
    exact_dups = int(clean.duplicated().sum())
    clean = clean.drop_duplicates().copy()

    clean["error_id_duplicado"] = clean["pedido_id"].duplicated(keep=False)
    clean["pendiente"] = clean["fecha_entrega"].isna()

    clean["error_cantidad"] = (
        clean["unidades_pedidas"].isna()
        | clean["unidades_pedidas"].le(0)
        | clean["unidades_entregadas"].lt(0)
        | (clean["unidades_entregadas"].isna() & ~clean["pendiente"])
        | (clean["unidades_entregadas"] > clean["unidades_pedidas"])
    )
    clean["error_costo"] = clean["costo_transporte"].isna() | clean["costo_transporte"].lt(0)
    clean["error_fechas"] = (
        clean["fecha_pedido"].isna()
        | clean["fecha_prometida"].isna()
        | (clean["fecha_prometida"] < clean["fecha_pedido"])
        | (clean["fecha_entrega"].notna() & (clean["fecha_entrega"] < clean["fecha_pedido"]))
    )

    audit = {
        "rows_input": n_before,
        "exact_duplicates_removed": exact_dups,
        "exact_duplicates_pct": round(100 * exact_dups / n_before, 2) if n_before else 0.0,
        "rows_after_dedup": len(clean),
    }
    for col in ERROR_COLS + ["pendiente"]:
        count = int(clean[col].sum())
        audit[col] = count
        audit[col + "_pct"] = round(100 * count / len(clean), 2) if len(clean) else 0.0
    return clean, audit


def split_valid(clean: pd.DataFrame, cutoff: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Split into (eligible valid orders, exceptions, exclusion audit).

    Eligible = no errors, not cancelled and promised date on or before the cutoff.
    Open orders that are not yet due are excluded; they are not failures.
    """
    cutoff_ts = pd.Timestamp(cutoff)
    has_error = clean[ERROR_COLS].any(axis=1)
    cancelled = clean["estado"].eq("CANCELADO").fillna(False).astype(bool)
    not_due = clean["fecha_prometida"] > cutoff_ts

    valid = clean.loc[~has_error & ~cancelled & ~not_due].copy()

    exceptions = clean.loc[has_error].copy()
    exceptions["motivo"] = exceptions[ERROR_COLS].apply(
        lambda r: ";".join(c.replace("error_", "") for c in ERROR_COLS if r[c]), axis=1)

    audit = {
        "excluded_cancelled": int((~has_error & cancelled).sum()),
        "excluded_not_yet_due": int((~has_error & ~cancelled & not_due).sum()),
        "exceptions": int(has_error.sum()),
        "eligible_orders": len(valid),
    }
    return valid, exceptions, audit
