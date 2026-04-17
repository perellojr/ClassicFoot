"""Registro central de eventos/notificações da carreira."""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class CareerEvent:
    timestamp: float
    kind: str
    message: str
    round_num: int | None = None
    season_year: int | None = None
    meta: dict | None = None


def ensure_career_event_log(career) -> list:
    log = getattr(career, "event_log", None)
    if not isinstance(log, list):
        log = []
        setattr(career, "event_log", log)
    return log


def append_career_notifications(
    career,
    messages: Iterable[str],
    *,
    kind: str = "news",
    round_num: int | None = None,
    season_year: int | None = None,
    dedupe_with_seen: bool = True,
):
    """
    Adiciona mensagens ao feed de notificações e ao log estruturado de eventos.
    Mantém compatibilidade com o fluxo atual (`career.notifications` + `seen_notifications`).
    """
    if not hasattr(career, "notifications") or not isinstance(career.notifications, list):
        career.notifications = []
    if not hasattr(career, "seen_notifications") or not isinstance(career.seen_notifications, set):
        career.seen_notifications = set()

    event_log = ensure_career_event_log(career)
    now = time.time()

    for raw_message in messages or []:
        message = str(raw_message or "").strip()
        if not message:
            continue
        if dedupe_with_seen and message in career.seen_notifications:
            continue

        career.notifications.append(message)
        if dedupe_with_seen:
            career.seen_notifications.add(message)

        event = CareerEvent(
            timestamp=now,
            kind=kind,
            message=message,
            round_num=round_num,
            season_year=season_year,
        )
        event_log.append(asdict(event))

