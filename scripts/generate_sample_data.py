#!/usr/bin/env python
"""Generate SYNTHETIC order data with intentional errors to test the pipeline.

All values are hypothetical and do not represent any company's results.
"""
import argparse

import numpy as np
import pandas as pd

CARRIERS = ["TRANSPORTES ANDINO", "RAPIDO PERU", "LOGISTICA SUR", "CARGO EXPRESS"]
WAREHOUSES = ["LIMA NORTE", "LIMA SUR", "CALLAO", "AREQUIPA"]
CUTOFF = pd.Timestamp("2026-06-30")


def build(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    order = pd.Timestamp("2026-01-01") + pd.to_timedelta(rng.integers(0, 181, n), unit="D")
    promised = order + pd.to_timedelta(rng.integers(2, 8, n), unit="D")
    delay = rng.choice([0] * 45 + [1, 2, 3, 5, 8], n)
    carrier = rng.choice(CARRIERS, n, p=[0.35, 0.25, 0.25, 0.15])
    # CARGO EXPRESS gets extra delays (a pattern for the carrier analysis).
    delay = delay + 3 * ((carrier == "CARGO EXPRESS") & (rng.random(n) < 0.25))
    delivered = promised + pd.to_timedelta(delay - rng.integers(0, 2, n), unit="D")

    ordered = rng.integers(10, 500, n)
    short = rng.random(n) > 0.96
    got = np.where(short, (ordered * rng.uniform(0.6, 0.99, n)).astype(int), ordered)

    df = pd.DataFrame({
        "pedido_id": [f"PED-{i:06d}" for i in range(1, n + 1)],
        "fecha_pedido": order, "fecha_prometida": promised, "fecha_entrega": delivered,
        "almacen": rng.choice(WAREHOUSES, n),
        "transportista": carrier,
        "unidades_pedidas": ordered, "unidades_entregadas": got.astype(float),
        "costo_transporte": np.round(rng.gamma(4, 12, n), 2),
        "estado": "ENTREGADO",
    })

    # Open orders: delivery after the cutoff, or randomly pending.
    open_mask = (df["fecha_entrega"] > CUTOFF) | (rng.random(n) < 0.01)
    df.loc[open_mask, ["fecha_entrega", "unidades_entregadas"]] = np.nan
    df.loc[open_mask, "estado"] = "PENDIENTE"
    df.loc[rng.random(n) < 0.01, "estado"] = "ANULADO"

    # --- Intentional errors ---
    def pick(frac):
        return rng.random(n) < frac

    df.loc[pick(0.003), "costo_transporte"] *= -1
    df.loc[pick(0.005), "costo_transporte"] = np.nan
    over = pick(0.004)
    df.loc[over & df["unidades_entregadas"].notna(), "unidades_entregadas"] += 25
    bad = pick(0.003) & df["fecha_entrega"].notna()
    df.loc[bad, "fecha_entrega"] = df.loc[bad, "fecha_pedido"] - pd.Timedelta(days=2)

    # Dates as dd/mm/yyyy text.
    for c in ["fecha_pedido", "fecha_prometida", "fecha_entrega"]:
        df[c] = df[c].dt.strftime("%d/%m/%Y")

    # Dirty labels: spaces, lowercase and aliases.
    dirty = pick(0.05)
    df.loc[dirty, "almacen"] = "  " + df.loc[dirty, "almacen"].str.lower() + " "
    alias = pick(0.04) & (df["transportista"] == "TRANSPORTES ANDINO")
    df.loc[alias, "transportista"] = "Transp. Andino"

    # Exact duplicates (1%) and conflicting duplicates with the same ID (0.5%).
    exact = df.sample(frac=0.01, random_state=seed)
    conflict = df.sample(frac=0.005, random_state=seed + 1).copy()
    conflict["costo_transporte"] = conflict["costo_transporte"].fillna(0) + 15
    df = pd.concat([df, exact, conflict], ignore_index=True)
    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output", default="data/raw/pedidos_logistica.csv")
    a = ap.parse_args()
    out = build(a.rows, a.seed)
    out.to_csv(a.output, index=False)
    print(f"Generated {len(out)} synthetic rows in {a.output}")
