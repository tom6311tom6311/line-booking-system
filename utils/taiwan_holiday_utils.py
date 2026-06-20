from datetime import date, timedelta


def _date_range(start_date, last_date):
  current_date = start_date
  while current_date <= last_date:
    yield current_date
    current_date += timedelta(days=1)


# Full Taiwan holiday periods, including weekend days inside a continuous break.
# Update this table when the official government work calendar is released.
TAIWAN_HOLIDAY_PERIODS = {
  2025: (
    (date(2025, 1, 1), date(2025, 1, 1)),
    (date(2025, 1, 25), date(2025, 2, 2)),
    (date(2025, 2, 28), date(2025, 3, 2)),
    (date(2025, 4, 3), date(2025, 4, 6)),
    (date(2025, 5, 1), date(2025, 5, 1)),
    (date(2025, 5, 30), date(2025, 6, 1)),
    (date(2025, 9, 27), date(2025, 9, 29)),
    (date(2025, 10, 4), date(2025, 10, 6)),
    (date(2025, 10, 10), date(2025, 10, 12)),
    (date(2025, 10, 24), date(2025, 10, 26)),
    (date(2025, 12, 25), date(2025, 12, 25)),
  ),
  2026: (
    (date(2026, 1, 1), date(2026, 1, 1)),
    (date(2026, 2, 14), date(2026, 2, 22)),
    (date(2026, 2, 27), date(2026, 3, 1)),
    (date(2026, 4, 3), date(2026, 4, 6)),
    (date(2026, 5, 1), date(2026, 5, 3)),
    (date(2026, 6, 19), date(2026, 6, 21)),
    (date(2026, 9, 25), date(2026, 9, 28)),
    (date(2026, 10, 9), date(2026, 10, 11)),
    (date(2026, 10, 24), date(2026, 10, 26)),
    (date(2026, 12, 25), date(2026, 12, 27)),
  ),
}

TAIWAN_HOLIDAYS = {
  holiday_date
  for periods in TAIWAN_HOLIDAY_PERIODS.values()
  for start_date, last_date in periods
  for holiday_date in _date_range(start_date, last_date)
}

# Saturdays/Sundays moved to working days by the official calendar.
TAIWAN_MAKEUP_WORKDAYS = {
  date(2025, 2, 8),
}


def is_taiwan_holiday(target_date):
  return target_date in TAIWAN_HOLIDAYS


def is_taiwan_workday(target_date):
  if target_date in TAIWAN_MAKEUP_WORKDAYS:
    return True
  return target_date.weekday() < 5 and not is_taiwan_holiday(target_date)


def is_booking_holiday_night(target_date):
  is_holiday = target_date.weekday() == 5 or is_taiwan_holiday(target_date)
  return is_holiday and not is_taiwan_workday(target_date + timedelta(days=1))
