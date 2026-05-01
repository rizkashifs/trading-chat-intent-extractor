from __future__ import annotations

import json

from .models import OUTPUT_COLUMNS
from .windowing import MessageWindow


SYSTEM_PROMPT = """You extract client trading intent from Bloomberg chat room messages.

Return only JSON. Do not include markdown.

Rules:
- Extract only actionable client order intent or order-status events.
- Use context across messages; client intent can be fragmented across several messages.
- Preserve trade jargon in order_message, but normalize fields when confident.
- side must be BUY, SELL, or blank if unknown.
- order_type must be Market, Limit, POV, or blank if unknown.
- event must be new or updated.
- close_reason must be confirmed, unconfirmed, limit not reached, or blank.
- trigger_type must be client initiated, market news initiated, or blank.
- confidence_score must be a number from 0 to 1.
- If a message contains mixed intent, return multiple order objects.
- If there is no client order intent, return {"orders": []}.
- Do not hallucinate product, quantity, price, or trigger details.
"""


def build_user_prompt(window: MessageWindow, client_ids: list[str] | None = None) -> str:
    messages = [
        {
            "row_number": message.row_number,
            "date": message.date,
            "time": message.time,
            "roomname": message.roomname,
            "sender": message.sender,
            "participants": message.participants,
            "message": message.message,
        }
        for message in window.messages
    ]
    payload = {
        "window_id": window.window_id,
        "roomname": window.roomname,
        "window_start": window.start_timestamp,
        "window_end": window.end_timestamp,
        "known_client_sender_ids": client_ids or [],
        "required_output_columns": OUTPUT_COLUMNS,
        "messages": messages,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
