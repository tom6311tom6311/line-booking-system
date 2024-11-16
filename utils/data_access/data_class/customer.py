from dataclasses import dataclass
from datetime import datetime

@dataclass
class Customer:
  customer_id: int = 0
  name: str = ''
  email: str = ''
  phone_number: str = ''
  address: str = ''
  relationship: str = ''
  notes: str = ''
  created: datetime = None
  modified: datetime = None
