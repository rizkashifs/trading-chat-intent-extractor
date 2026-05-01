from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


OUTPUT_COLUMNS = [
    "order_id",
    "date",
    "chat_timestamp",
    "roomname",
    "client_sender_id",
    "product",
    "side",
    "quantity",
    "order_type",
    "price",
    "event",
    "order_message",
    "order_time",
    "close_reason",
    "trigger_type",
    "trigger_explanation",
    "confidence_score",
]


@dataclass(frozen=True)
class ChatMessage:
    date: str
    time: str
    roomname: str
    sender: str
    participants: list[str]
    message: str
    row_number: int

    @property
    def timestamp_text(self) -> str:
        return f"{self.date} {self.time}".strip()

    @property
    def timestamp(self) -> datetime:
        text = self.timestamp_text
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d-%m-%Y %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                pass
        return datetime.max


@dataclass
class OrderEvent:
    order_id: str
    date: str
    chat_timestamp: str
    roomname: str
    client_sender_id: str
    product: str
    side: str
    quantity: str
    order_type: str
    price: str
    event: str
    order_message: str
    order_time: str
    close_reason: str
    trigger_type: str
    trigger_explanation: str
    confidence_score: float

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "OrderEvent":
        normalized = {column: data.get(column, "") for column in OUTPUT_COLUMNS}
        normalized["side"] = str(normalized["side"]).upper()
        normalized["event"] = str(normalized["event"]).lower()
        normalized["confidence_score"] = _coerce_confidence(normalized["confidence_score"])
        return cls(**normalized)

    def to_row(self) -> dict[str, Any]:
        return {column: getattr(self, column) for column in OUTPUT_COLUMNS}


def _coerce_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, confidence))
