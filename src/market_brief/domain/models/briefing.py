from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class BriefingItem:
    title: str
    source: str
    url: str
    timestamp: datetime
    timestamp_label: str


@dataclass(frozen=True)
class Briefing:
    items: tuple[BriefingItem, ...]