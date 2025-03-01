import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Any

@dataclass
class BookingInfo:
  booking_id: int
  status: str
  customer_name: str
  phone_number: str
  check_in_date: date
  last_date: date
  total_price: float
  notes: str
  source: str
  prepayment: float
  prepayment_note: str
  prepayment_status: str
  room_ids: str
  created: datetime = None
  modified: datetime = None

  def __hash__(self):
    return hash((
      self.booking_id, self.status, self.customer_name, self.phone_number, 
      self.check_in_date, self.last_date, self.total_price, self.notes, 
      self.source, self.prepayment, self.prepayment_note, self.prepayment_status, 
      self.room_ids
    ))

  def __eq__(self, other):
    if not isinstance(other, BookingInfo):
      return NotImplemented
    return (
      self.booking_id == other.booking_id and
      self.status == other.status and
      self.customer_name == other.customer_name and
      self.phone_number == other.phone_number and
      self.check_in_date == other.check_in_date and
      self.last_date == other.last_date and
      int(self.total_price) == int(other.total_price) and
      self.notes == other.notes and
      self.source == other.source and
      int(self.prepayment) == int(other.prepayment) and
      self.prepayment_note == other.prepayment_note and
      self.prepayment_status == other.prepayment_status and
      self.room_ids == other.room_ids
    )

  def __sub__(self, other) -> Dict[str, Any]:
    """Returns the differences between two BookingInfo objects as a dictionary."""
    if not isinstance(other, BookingInfo):
      raise TypeError("Subtraction is only supported between BookingInfo objects")

    differences = {}

    for field in BookingInfo.__dataclass_fields__:
      if field in { "created", "modified" }:  # Ignore timestamps
        continue

      old_value = getattr(self, field)
      new_value = getattr(other, field)

      if isinstance(old_value, float) or isinstance(new_value, float):
        if (int(old_value) != int(new_value)):
          differences[field] = { "old": old_value, "new": new_value }
      elif old_value != new_value:
        differences[field] = { "old": old_value, "new": new_value }

    return differences
