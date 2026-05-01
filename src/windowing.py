from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import count

from .models import ChatMessage


@dataclass(frozen=True)
class MessageWindow:
    window_id: str
    roomname: str
    messages: list[ChatMessage]

    @property
    def start_timestamp(self) -> str:
        return self.messages[0].timestamp_text if self.messages else ""

    @property
    def end_timestamp(self) -> str:
        return self.messages[-1].timestamp_text if self.messages else ""


def build_room_windows(
    messages: list[ChatMessage],
    room_filter: str | None = None,
    window_size: int = 12,
    overlap: int = 4,
) -> list[MessageWindow]:
    if window_size < 1:
        raise ValueError("window_size must be at least 1")
    if overlap < 0 or overlap >= window_size:
        raise ValueError("overlap must be >= 0 and smaller than window_size")

    grouped: dict[str, list[ChatMessage]] = defaultdict(list)
    for message in messages:
        if room_filter and message.roomname != room_filter:
            continue
        grouped[message.roomname].append(message)

    windows: list[MessageWindow] = []
    ids = count(1)
    step = window_size - overlap
    for roomname in sorted(grouped):
        room_messages = sorted(grouped[roomname], key=lambda item: (item.timestamp, item.row_number))
        for start in range(0, len(room_messages), step):
            chunk = room_messages[start : start + window_size]
            if not chunk:
                continue
            windows.append(MessageWindow(f"window-{next(ids):06d}", roomname, chunk))
            if start + window_size >= len(room_messages):
                break
    return windows
