from __future__ import annotations

import argparse
from pathlib import Path

from .client_catalog import merge_client_ids, read_client_ids
from .env_loader import load_env_file
from .pipeline import extract_orders_from_csv


def main() -> None:
    load_env_file()

    parser = argparse.ArgumentParser(description="Extract client order intent from Bloomberg chat CSV data.")
    parser.add_argument("--input", required=True, type=Path, help="Input chat CSV path")
    parser.add_argument("--output", required=True, type=Path, help="Final output orders CSV path")
    parser.add_argument("--room", default=None, help="Optional roomname filter")
    parser.add_argument("--client-ids", default="", help="Comma-separated known client sender IDs")
    parser.add_argument(
        "--clients",
        default=Path("data/client_ids.csv"),
        type=Path,
        help="CSV with known client sender IDs",
    )
    parser.add_argument(
        "--products",
        default=Path("data/traded_products.csv"),
        type=Path,
        help="CSV with product and optional aliases columns",
    )
    parser.add_argument("--window-size", default=12, type=int, help="Messages per LLM context window")
    parser.add_argument("--overlap", default=4, type=int, help="Overlapping messages between windows")
    parser.add_argument("--max-windows", default=None, type=int, help="Optional cap for quick POC runs")
    parser.add_argument("--debug-dir", default=None, type=Path, help="Optional debug folder for prompts and responses")
    parser.add_argument("--log-file", default=None, type=Path, help="Optional CSV log path")
    parser.add_argument("--dry-run", action="store_true", help="Print LLM prompts without calling the gateway")
    args = parser.parse_args()
    client_ids = merge_client_ids(read_client_ids(args.clients), _parse_client_ids(args.client_ids))

    orders = extract_orders_from_csv(
        input_path=args.input,
        output_path=args.output,
        room_filter=args.room,
        client_ids=client_ids,
        window_size=args.window_size,
        overlap=args.overlap,
        products_path=args.products,
        max_windows=args.max_windows,
        debug_dir=args.debug_dir,
        log_file=args.log_file,
        dry_run=args.dry_run,
    )
    if not args.dry_run:
        print(f"Wrote {len(orders)} orders to {args.output}")


def _parse_client_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    main()
