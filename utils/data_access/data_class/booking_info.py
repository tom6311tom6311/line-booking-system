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
