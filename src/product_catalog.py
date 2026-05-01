from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProductCatalog:
    products: dict[str, str]

    @classmethod
    def from_csv(cls, path: Path) -> "ProductCatalog":
        if not path.exists():
            return cls(products={})

        products: dict[str, str] = {}
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise ValueError(f"{path} must have a header row")

            symbol_column = _find_symbol_column(reader.fieldnames)
            if symbol_column is None:
                raise ValueError(f"{path} must have a 'Symbol' column")

            for row in reader:
                canonical = (row.get(symbol_column) or "").strip().upper()
                if not canonical:
                    continue

                key = normalize_product_text(canonical)
                if key:
                    products[key] = canonical

        return cls(products=products)

    def resolve(self, value: str) -> str:
        key = normalize_product_text(value)
        if not key:
            return value

        exact = self.products.get(key)
        if exact:
            return exact

        prefix_matches = {canonical for alias, canonical in self.products.items() if alias.startswith(key)}
        if len(prefix_matches) == 1:
            return next(iter(prefix_matches))

        return value


def normalize_product_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _find_symbol_column(fieldnames: list[str]) -> str | None:
    for fieldname in fieldnames:
        if fieldname.lower() == "symbol":
            return fieldname
    for fieldname in fieldnames:
        if fieldname.lower() == "product":
            return fieldname
    return None
