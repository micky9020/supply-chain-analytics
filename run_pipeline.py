#!/usr/bin/env python
"""Usage: python run_pipeline.py --input data/raw/pedidos_logistica.csv --output-dir outputs"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from supply_chain.config import Config      # noqa: E402
from supply_chain.pipeline import run       # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Data quality and logistics KPI pipeline")
    p.add_argument("--input", default="data/raw/pedidos_logistica.csv")
    p.add_argument("--output-dir", default="outputs")
    p.add_argument("--cutoff", default=None, help="Cutoff date YYYY-MM-DD")
    p.add_argument("--date-format", default=None, help="Date format, e.g. %%d/%%m/%%Y")
    p.add_argument("--investment", type=float, default=None, help="One-time project investment (S/)")
    a = p.parse_args()

    cfg = Config()
    if a.cutoff:
        cfg.cutoff = a.cutoff
    if a.date_format:
        cfg.date_format = a.date_format

    if a.investment is not None:
        cfg.investment = a.investment

    audit = run(a.input, a.output_dir, cfg)
    print(json.dumps(audit["headline"], indent=2))
    print(f"\nResults written to: {a.output_dir}/")


if __name__ == "__main__":
    main()
