from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Any

@dataclass
class ClosureInfo:
  closure_id: int
  status: str
  start_date: date
  last_date: date
  reason: str
  room_ids: str
  created: datetime = None
  modified: datetime = None
  notion_page_id: str = None

  def __hash__(self):
    return hash((self.status, self.start_date, self.last_date, self.reason, self.room_ids))

  def __eq__(self, other):
    if not isinstance(other, ClosureInfo):
      return NotImplemented
    return (
      self.status == other.status and
      self.start_date == other.start_date and
      self.last_date == other.last_date and
      self.reason == other.reason and
      self.room_ids == other.room_ids
    )

  def __sub__(self, other) -> Dict[str, Any]:
    """Returns the differences between two ClosureInfo objects as a dictionary."""
    if not isinstance(other, ClosureInfo):
      raise TypeError("Subtraction is only supported between ClosureInfo objects")

    differences = {}

    for field in ClosureInfo.__dataclass_fields__:
      if field in { "closure_id", "created", "modified", "notion_page_id" }:  # Ignore these fields
        continue

      old_value = getattr(self, field)
      new_value = getattr(other, field)

      if old_value != new_value:
        differences[field] = { "old": old_value, "new": new_value }

    return differences
