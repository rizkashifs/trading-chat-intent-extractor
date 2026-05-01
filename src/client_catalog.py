from __future__ import annotations

import csv
from pathlib import Path


def read_client_ids(path: Path | None) -> list[str]:
    if path is None or not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"{path} must have a header row")

        id_column = _find_id_column(reader.fieldnames)
        if id_column is None:
            raise ValueError(f"{path} must have a 'client_sender_id' column")

        return _dedupe((row.get(id_column) or "").strip() for row in reader)


def merge_client_ids(*groups: list[str]) -> list[str]:
    return _dedupe(client_id.strip() for group in groups for client_id in group if client_id.strip())


def _find_id_column(fieldnames: list[str]) -> str | None:
    for fieldname in fieldnames:
        if fieldname.lower() in {"client_sender_id", "client_id", "sender"}:
            return fieldname
    return None


def _dedupe(values: object) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
