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

  def __hash__(self):
    return hash((self.start_date, self.last_date, self.room_ids))

  def __eq__(self, other):
    if not isinstance(other, ClosureInfo):
      return NotImplemented
    return (
      self.start_date == other.start_date and
      self.last_date == other.last_date and
      self.reason == other.reason and
      self.room_ids == other.room_ids
    )
