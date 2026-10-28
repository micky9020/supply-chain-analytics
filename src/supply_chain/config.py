"""Analysis parameters. Adjust these values to your real business."""
from dataclasses import dataclass, field


@dataclass
class Config:
    # Actual date format in the source CSV (confirm it before running).
    date_format: str = "%d/%m/%Y"
    # Report cutoff date (normally the data extraction date).
    cutoff: str = "2026-06-30"
    otif_target: float = 0.95
    # One-time improvement investment (S/) and cost-reduction scenarios.
    investment: float = 30_000.0
    scenarios: dict = field(default_factory=lambda: {
        "Conservative": 0.03, "Base case": 0.05, "Upside": 0.08})
    # Alias -> approved label (example values: replace with the business list).
    carrier_map: dict = field(default_factory=lambda: {
        "TRANSP. ANDINO": "TRANSPORTES ANDINO",
        "T. ANDINO": "TRANSPORTES ANDINO",
    })
    status_map: dict = field(default_factory=lambda: {
        "ENTREG.": "ENTREGADO",
        "ANULADO": "CANCELADO",
    })
