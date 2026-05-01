from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .models import OrderEvent
from .product_catalog import ProductCatalog
from .windowing import MessageWindow


def parse_llm_orders(
    raw_response: str,
    window: MessageWindow,
    product_catalog: ProductCatalog | None = None,
) -> list[OrderEvent]:
    payload = _load_json_object(raw_response)
    raw_orders = payload.get("orders", [])
    if not isinstance(raw_orders, list):
        raise ValueError("LLM response field 'orders' must be a list")

    orders = []
    for raw_order in raw_orders:
        if not isinstance(raw_order, dict):
            continue
        enriched = _with_window_defaults(raw_order, window, product_catalog)
        orders.append(OrderEvent.from_mapping(enriched))
    return orders


def _load_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        return {"orders": []}

    try:
        loaded = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            raise
        loaded = json.loads(match.group(0))

    if not isinstance(loaded, dict):
        raise ValueError("LLM response must be a JSON object")
    return loaded


def _with_window_defaults(
    order: dict[str, Any],
    window: MessageWindow,
    product_catalog: ProductCatalog | None,
) -> dict[str, Any]:
    first = window.messages[0]
    data = dict(order)
    if product_catalog and data.get("product"):
        data["product"] = product_catalog.resolve(str(data["product"]))
    data.setdefault("date", first.date)
    data.setdefault("chat_timestamp", first.timestamp_text)
    data.setdefault("roomname", window.roomname)
    data.setdefault("event", "new")
    data.setdefault("close_reason", "unconfirmed")
    data.setdefault("trigger_type", "client initiated")
    data["order_id"] = data.get("order_id") or _stable_order_id(data, window)
    return data


def _stable_order_id(order: dict[str, Any], window: MessageWindow) -> str:
    parts = [
        window.roomname,
        str(order.get("client_sender_id", "")),
        str(order.get("product", "")),
        str(order.get("side", "")),
        str(order.get("quantity", "")),
        str(order.get("order_time", "")),
        str(order.get("order_message", "")),
    ]
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"ord_{digest}"
