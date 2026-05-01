from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .models import ChatMessage, OrderEvent
from .windowing import MessageWindow


LOG_COLUMNS = [
    "event_type",
    "window_id",
    "roomname",
    "row_number",
    "chat_timestamp",
    "sender",
    "order_id",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "details",
]


class RunLogger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("w", encoding="utf-8", newline="")
        self.writer = csv.DictWriter(self.file, fieldnames=LOG_COLUMNS)
        self.writer.writeheader()

    def log_input_row(self, window: MessageWindow, message: ChatMessage) -> None:
        self._write(
            event_type="input_row_analyzed",
            window_id=window.window_id,
            roomname=window.roomname,
            row_number=message.row_number,
            chat_timestamp=message.timestamp_text,
            sender=message.sender,
            details=message.message,
        )

    def log_prompt_usage(
        self,
        window: MessageWindow,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        total_tokens: int | None,
    ) -> None:
        self._write(
            event_type="prompt_usage",
            window_id=window.window_id,
            roomname=window.roomname,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    def log_output_order(self, window: MessageWindow, order: OrderEvent) -> None:
        self._write(
            event_type="output_order_created",
            window_id=window.window_id,
            roomname=window.roomname,
            order_id=order.order_id,
            details=(
                f"{order.event} {order.side} {order.quantity} {order.product} "
                f"client={order.client_sender_id} confidence={order.confidence_score}"
            ).strip(),
        )

    def log_error(self, window: MessageWindow, details: str) -> None:
        self._write(
            event_type="window_error",
            window_id=window.window_id,
            roomname=window.roomname,
            details=details,
        )

    def close(self) -> None:
        self.file.close()

    def _write(self, **row: Any) -> None:
        self.writer.writerow({column: row.get(column, "") for column in LOG_COLUMNS})
        self.file.flush()
