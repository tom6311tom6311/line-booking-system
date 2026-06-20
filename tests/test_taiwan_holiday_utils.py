import unittest
from datetime import date

from utils.taiwan_holiday_utils import (
  is_booking_holiday_night,
  is_taiwan_workday,
)


class TaiwanHolidayUtilsTest(unittest.TestCase):
  def test_saturday_keeps_existing_holiday_pricing(self):
    self.assertTrue(is_booking_holiday_night(date(2026, 6, 13)))

  def test_regular_sunday_before_monday_workday_is_not_holiday_priced(self):
    self.assertFalse(is_booking_holiday_night(date(2026, 6, 14)))

  def test_holiday_period_day_before_another_holiday_is_holiday_priced(self):
    self.assertTrue(is_booking_holiday_night(date(2026, 2, 15)))

  def test_last_holiday_period_day_before_workday_is_not_holiday_priced(self):
    self.assertFalse(is_booking_holiday_night(date(2026, 2, 22)))

  def test_single_holiday_before_workday_is_not_holiday_priced(self):
    self.assertFalse(is_booking_holiday_night(date(2026, 1, 1)))

  def test_holiday_observed_monday_is_not_a_workday(self):
    self.assertFalse(is_taiwan_workday(date(2026, 4, 6)))


if __name__ == '__main__':
  unittest.main()
