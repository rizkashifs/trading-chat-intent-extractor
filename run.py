from __future__ import annotations

import os
from pathlib import Path

from src.client_catalog import merge_client_ids, read_client_ids
from src.env_loader import load_env_file
from src.pipeline import extract_orders_from_csv


def main() -> None:
    load_env_file()

    input_path = Path(_env("INPUT_CSV", "data/sample_chat.csv"))
    output_path = Path(_env("OUTPUT_CSV", "out/orders.csv"))
    clients_path = Path(_env("CLIENT_IDS_CSV", "data/client_ids.csv"))
    products_path = Path(_env("TRADED_PRODUCTS_CSV", "data/traded_products.csv"))
    log_file = Path(_env("LOG_CSV", str(output_path.with_suffix(".log.csv"))))
    debug_dir = _optional_path(os.getenv("DEBUG_DIR"))

    client_ids = merge_client_ids(
        read_client_ids(clients_path),
        _csv_env("CLIENT_IDS"),
    )

    orders = extract_orders_from_csv(
        input_path=input_path,
        output_path=output_path,
        room_filter=os.getenv("ROOM_FILTER") or None,
        client_ids=client_ids,
        window_size=_int_env("WINDOW_SIZE", 12),
        overlap=_int_env("WINDOW_OVERLAP", 4),
        products_path=products_path,
        max_windows=_optional_int(os.getenv("MAX_WINDOWS")),
        debug_dir=debug_dir,
        log_file=log_file,
        dry_run=_bool_env("DRY_RUN", False),
    )

    if not _bool_env("DRY_RUN", False):
        print(f"Wrote {len(orders)} orders to {output_path}")
    print(f"Run log: {log_file}")


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def _csv_env(name: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    return int(value)


def _optional_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(value)


def _optional_path(value: str | None) -> Path | None:
    if value is None or not value.strip():
        return None
    return Path(value)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


if __name__ == "__main__":
    main()
