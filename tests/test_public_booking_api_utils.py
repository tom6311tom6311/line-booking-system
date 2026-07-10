import unittest
import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.modules.setdefault("flask", SimpleNamespace(jsonify=lambda payload: payload, request=SimpleNamespace()))
sys.modules.setdefault("utils.datetime_utils", SimpleNamespace(get_local_today=lambda: date.today()))

from utils.public_booking_api_utils import (
  ensure_public_bookable_date_range,
  ensure_rooms_available,
  is_public_bookable_date_range,
  parse_date_range,
)


class PublicBookingApiUtilsTest(unittest.TestCase):
  def test_regular_monday_night_is_not_public_bookable(self):
    self.assertFalse(is_public_bookable_date_range(date(2026, 7, 6), date(2026, 7, 6)))

  def test_holiday_monday_night_is_public_bookable(self):
    self.assertTrue(is_public_bookable_date_range(date(2026, 4, 6), date(2026, 4, 6)))

  def test_range_with_regular_tuesday_night_is_not_public_bookable(self):
    self.assertFalse(is_public_bookable_date_range(date(2026, 7, 5), date(2026, 7, 7)))

  def test_ensure_public_bookable_date_range_raises_chinese_error(self):
    with self.assertRaisesRegex(ValueError, "週一、週二、週三"):
      ensure_public_bookable_date_range(date(2026, 7, 6), date(2026, 7, 6))

  def test_ensure_rooms_available_rejects_closed_weekday_before_querying_dao(self):
    booking_dao = Mock()

    with self.assertRaisesRegex(ValueError, "週一、週二、週三"):
      ensure_rooms_available(["稻"], date(2026, 7, 6), date(2026, 7, 6), booking_dao)

    booking_dao.get_available_room_ids.assert_not_called()

  @patch("utils.public_booking_api_utils.get_local_today", return_value=date(2026, 7, 10))
  def test_parse_date_range_allows_check_in_180_days_from_today(self, _):
    check_in, check_out, last_date, nights = parse_date_range({
      "checkIn": "2027-01-06",
      "checkOut": "2027-01-07",
    })

    self.assertEqual(check_in, date(2027, 1, 6))
    self.assertEqual(check_out, date(2027, 1, 7))
    self.assertEqual(last_date, date(2027, 1, 6))
    self.assertEqual(nights, 1)

  @patch("utils.public_booking_api_utils.get_local_today", return_value=date(2026, 7, 10))
  def test_parse_date_range_rejects_check_in_more_than_180_days_from_today(self, _):
    with self.assertRaisesRegex(ValueError, "180 天內"):
      parse_date_range({
        "checkIn": "2027-01-07",
        "checkOut": "2027-01-08",
      })


if __name__ == "__main__":
  unittest.main()
