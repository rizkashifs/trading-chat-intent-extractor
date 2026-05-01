from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import ChatMessage


REQUIRED_COLUMNS = {"date", "time", "roomname", "sender", "participants", "message"}


def read_chat_csv(path: Path) -> list[ChatMessage]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no header row")

        missing = REQUIRED_COLUMNS.difference(reader.fieldnames)
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ValueError(f"{path} is missing required columns: {missing_text}")

        messages = []
        for row_number, row in enumerate(reader, start=2):
            messages.append(
                ChatMessage(
                    date=(row.get("date") or "").strip(),
                    time=(row.get("time") or "").strip(),
                    roomname=(row.get("roomname") or "").strip(),
                    sender=(row.get("sender") or "").strip(),
                    participants=parse_participants(row.get("participants") or ""),
                    message=(row.get("message") or "").strip(),
                    row_number=row_number,
                )
            )
    return messages


def parse_participants(value: str) -> list[str]:
    text = value.strip()
    if not text:
        return []

    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]

    delimiter = ";" if ";" in text else ","
    return [part.strip() for part in text.split(delimiter) if part.strip()]
