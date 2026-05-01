from __future__ import annotations

import csv
from pathlib import Path

from .extraction_parser import parse_llm_orders
from .input_reader import read_chat_csv
from .llm_client import LlmExtractor
from .models import OUTPUT_COLUMNS, OrderEvent
from .product_catalog import ProductCatalog
from .prompting import build_user_prompt
from .run_logger import RunLogger
from .windowing import MessageWindow, build_room_windows


def extract_orders_from_csv(
    input_path: Path,
    output_path: Path,
    room_filter: str | None = None,
    client_ids: list[str] | None = None,
    window_size: int = 12,
    overlap: int = 4,
    products_path: Path | None = None,
    max_windows: int | None = None,
    debug_dir: Path | None = None,
    log_file: Path | None = None,
    dry_run: bool = False,
) -> list[OrderEvent]:
    messages = read_chat_csv(input_path)
    product_catalog = ProductCatalog.from_csv(products_path) if products_path else ProductCatalog(products={})
    windows = build_room_windows(messages, room_filter=room_filter, window_size=window_size, overlap=overlap)
    if max_windows is not None:
        windows = windows[:max_windows]

    print(f"Loaded {len(messages)} messages")
    print(f"Loaded {len(set(product_catalog.products.values()))} traded products")
    print(f"Built {len(windows)} windows")

    run_logger = RunLogger(log_file or output_path.with_suffix(".log.csv"))
    try:
        if dry_run:
            for window in windows:
                log_window_input_rows(run_logger, window)
                prompt = build_user_prompt(window, client_ids=client_ids)
                if debug_dir:
                    write_debug_file(debug_dir, f"{window.window_id}.prompt.json", prompt)
                else:
                    print(prompt)
            return []

        extractor = LlmExtractor()
        orders: list[OrderEvent] = []
        seen_order_ids: set[str] = set()
        for index, window in enumerate(windows, start=1):
            print(f"Extracting {index}/{len(windows)}: {window.window_id} {window.roomname}")
            log_window_input_rows(run_logger, window)
            prompt = build_user_prompt(window, client_ids=client_ids)
            if debug_dir:
                write_debug_file(debug_dir, f"{window.window_id}.prompt.json", prompt)

            response = extractor.extract_window(window, client_ids=client_ids)
            run_logger.log_prompt_usage(
                window,
                prompt_tokens=response.prompt_tokens,
                completion_tokens=response.completion_tokens,
                total_tokens=response.total_tokens,
            )
            if debug_dir:
                write_debug_file(debug_dir, f"{window.window_id}.response.json", response.content)

            try:
                parsed_orders = parse_llm_orders(response.content, window, product_catalog=product_catalog)
            except Exception as exc:
                message = f"could not parse LLM response ({exc})"
                print(f"Skipping {window.window_id}: {message}")
                run_logger.log_error(window, message)
                continue

            for order in parsed_orders:
                if order.order_id in seen_order_ids:
                    continue
                seen_order_ids.add(order.order_id)
                orders.append(order)
                run_logger.log_output_order(window, order)
            print(f"  found {len(parsed_orders)} orders")
    finally:
        run_logger.close()

    write_orders_csv(output_path, orders)
    return orders


def write_orders_csv(path: Path, orders: list[OrderEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for order in orders:
            writer.writerow(order.to_row())


def write_debug_file(path: Path, filename: str, content: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / filename).write_text(content, encoding="utf-8")


def log_window_input_rows(run_logger: RunLogger, window: MessageWindow) -> None:
    for message in window.messages:
        run_logger.log_input_row(window, message)
