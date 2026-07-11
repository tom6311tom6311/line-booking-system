import sys
import unittest
from datetime import date
from types import SimpleNamespace

sys.modules.setdefault("utils.datetime_utils", SimpleNamespace(get_local_today=lambda: date.today()))

from utils.booking_utils import get_booking_room_brief


class BookingUtilsTest(unittest.TestCase):
  def test_get_booking_room_brief_without_extra_bed(self):
    self.assertEqual(
      get_booking_room_brief({"standard_double_room": 2, "standard_family_room": 1}),
      "雙人套房2間、四人套房1間",
    )

  def test_get_booking_room_brief_with_extra_bed(self):
    self.assertEqual(
      get_booking_room_brief({"standard_double_room": 1}, 2),
      "雙人套房1間、共加2床",
    )


if __name__ == "__main__":
  unittest.main()
