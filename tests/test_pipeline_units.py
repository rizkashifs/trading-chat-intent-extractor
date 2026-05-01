from __future__ import annotations

from src.extraction_parser import parse_llm_orders
from src.input_reader import parse_participants
from src.models import ChatMessage
from src.product_catalog import ProductCatalog
from src.windowing import MessageWindow, build_room_windows


def test_parse_participants_variants() -> None:
    assert parse_participants('["a", "b"]') == ["a", "b"]
    assert parse_participants("a;b") == ["a", "b"]
    assert parse_participants("a,b") == ["a", "b"]


def test_build_room_windows_preserves_room_order() -> None:
    messages = [
        ChatMessage("2026-04-29", "09:02:00", "room", "c", [], "three", 3),
        ChatMessage("2026-04-29", "09:00:00", "room", "c", [], "one", 1),
        ChatMessage("2026-04-29", "09:01:00", "room", "c", [], "two", 2),
    ]
    windows = build_room_windows(messages, window_size=2, overlap=1)
    assert [message.message for message in windows[0].messages] == ["one", "two"]
    assert [message.message for message in windows[1].messages] == ["two", "three"]


def test_parse_llm_orders_defaults_and_confidence() -> None:
    window = MessageWindow(
        "window-1",
        "room",
        [ChatMessage("2026-04-29", "09:00:00", "room", "client", [], "Buy 100 IBM", 1)],
    )
    raw = """
    {"orders": [{
      "client_sender_id": "client",
      "product": "IBM",
      "side": "buy",
      "quantity": "100 shares",
      "confidence_score": 2
    }]}
    """
    orders = parse_llm_orders(raw, window)
    assert len(orders) == 1
    assert orders[0].side == "BUY"
    assert orders[0].confidence_score == 1.0
    assert orders[0].roomname == "room"
    assert orders[0].order_id.startswith("ord_")


def test_parse_llm_orders_maps_product_alias() -> None:
    window = MessageWindow(
        "window-1",
        "room",
        [ChatMessage("2026-04-29", "09:00:00", "room", "client", [], "Compra 4k lul", 1)],
    )
    catalog = ProductCatalog(products={"lulu": "LULU"})
    raw = '{"orders": [{"client_sender_id": "client", "product": "lul", "confidence_score": 0.8}]}'

    orders = parse_llm_orders(raw, window, product_catalog=catalog)

    assert orders[0].product == "LULU"
