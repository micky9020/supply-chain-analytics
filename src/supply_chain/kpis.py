"""OTIF, delay, cost-per-order calculations and segment summaries."""
import pandas as pd


def add_kpis(valid: pd.DataFrame, cutoff: str) -> pd.DataFrame:
    """Add delivery metrics. An open order that is already overdue counts as a failure."""
    cutoff_ts = pd.Timestamp(cutoff)
    out = valid.copy()
    out["entrega_completa"] = out["unidades_entregadas"] >= out["unidades_pedidas"]
    out["entrega_a_tiempo"] = (
        out["fecha_entrega"].notna() & (out["fecha_entrega"] <= out["fecha_prometida"])
    )
    out["otif"] = out["entrega_completa"] & out["entrega_a_tiempo"]

    end_date = out["fecha_entrega"].fillna(cutoff_ts)
    out["dias_retraso"] = (end_date - out["fecha_prometida"]).dt.days.clip(lower=0)

    # The period is the PROMISED month, not the order creation month.
    out["mes"] = out["fecha_prometida"].dt.to_period("M").astype(str)
    out["costo_por_unidad"] = out["costo_transporte"] / out["unidades_pedidas"]
    return out


def summarize(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """Summary by segment (month, warehouse, carrier, ...)."""
    out = (
        df.groupby(key)
        .agg(
            orders=("pedido_id", "nunique"),
            cost=("costo_transporte", "sum"),
            units=("unidades_pedidas", "sum"),
            otif=("otif", "mean"),
            average_delay_days=("dias_retraso", "mean"),
        )
        .reset_index()
    )
    out["otif_pct"] = out["otif"] * 100
    out["cost_per_order"] = out["cost"] / out["orders"]
    return out.drop(columns="otif")


def headline(df: pd.DataFrame, target: float) -> dict:
    """Overall executive indicators."""
    n = df["pedido_id"].nunique()
    otif_orders = int(df["otif"].sum())
    return {
        "orders": n,
        "total_cost": round(float(df["costo_transporte"].sum()), 2),
        "cost_per_order": round(float(df["costo_transporte"].sum() / n), 2) if n else None,
        "otif_orders": otif_orders,
        "otif_pct": round(100 * otif_orders / n, 2) if n else None,
        "gap_to_target_pp": round(100 * (target - otif_orders / n), 2) if n else None,
    }
