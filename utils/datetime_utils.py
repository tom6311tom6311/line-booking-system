import os
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta

APP_TIMEZONE = ZoneInfo(os.getenv('APP_TIMEZONE', 'Asia/Taipei'))


def get_local_now():
  return datetime.now(APP_TIMEZONE)


def get_local_today():
  return get_local_now().date()


# Generate the last n months im the specified format including the current month
def get_latest_months(num=3, format='%Y-%m'):
  current_date = get_local_now()
  return [(current_date - relativedelta(months=i)).strftime(format) for i in range(num)]
