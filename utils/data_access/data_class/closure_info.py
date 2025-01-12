from dataclasses import dataclass
from datetime import date, datetime

@dataclass
class ClosureInfo:
  closure_id: int
  start_date: date
  last_date: date
  reason: str
  room_ids: str
  created: datetime = None
  modified: datetime = None
  notion_page_id: str = None
