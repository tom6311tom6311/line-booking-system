from dataclasses import dataclass
from datetime import date, datetime

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

  def __str__(self):
    return f"{self.booking_id}, {self.status}, {self.customer_name}, {self.phone_number}, {self.check_in_date}, {self.last_date}, {self.total_price}, {self.notes}, {self.source}, {self.prepayment}, {self.prepayment_note}, {self.prepayment_status}, {self.room_ids}"

  def __hash__(self):
    return self.booking_id

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
      self.total_price == other.total_price and
      self.notes == other.notes and
      self.source == other.source and
      self.prepayment == other.prepayment and
      self.prepayment_note == other.prepayment_note and
      self.prepayment_status == other.prepayment_status and
      self.room_ids == other.room_ids
    )
