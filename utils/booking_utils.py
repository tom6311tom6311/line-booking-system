import datetime
import typing
from const.booking_const import GENERIC_NAMES, BOOKING_STATUS_MARK, PREPAYMENT_STATUS_MAP
from utils.data_access.data_class.booking_info import BookingInfo

# Function to format the booking info as per the required format
def format_booking_info(booking_info: typing.Optional[BookingInfo]=None, variant='normal'):
  if not booking_info:
    return None

  if booking_info.phone_number.startswith('+886'):
    booking_info.phone_number = '0' + booking_info.phone_number[4:]
  total_price = int(booking_info.total_price)
  prepayment = int(booking_info.prepayment)

  status_mark = BOOKING_STATUS_MARK[booking_info.status] if booking_info.status in BOOKING_STATUS_MARK else ''

  # Calculate the number of nights
  nights = (booking_info.last_date - booking_info.check_in_date).days + 1
  check_out_date = booking_info.last_date + datetime.timedelta(days=1)

  booking_info.prepayment_status = PREPAYMENT_STATUS_MAP[booking_info.prepayment_status]

  # Format the response message
  message = ""
  if variant == 'carousel':
    message = (
    f"姓名：{booking_info.customer_name}\n"
    f"電話：{booking_info.phone_number}\n"
    f"入住：{booking_info.check_in_date.strftime('%Y/%m/%d')}\n"
    f"晚數：{nights}\n"
    f"總金額：{total_price}\n"
  )
  elif variant == 'calendar':
    message = (
      f"ＩＤ：{booking_info.booking_id}\n"
      f"電話：{booking_info.phone_number}\n"
      f"訂金：{prepayment}元/{booking_info.prepayment_status}\n"
      f"來源：{booking_info.source}\n"
      f"備註：{booking_info.notes}\n"
    )
  else:
    message = (
      f"[訂單]{status_mark}\n"
      f"ＩＤ：{booking_info.booking_id}\n"
      f"姓名：{booking_info.customer_name}\n"
      f"電話：{booking_info.phone_number}\n"
      f"入住日期：{booking_info.check_in_date.strftime('%Y/%m/%d')}\n"
      f"退房日期：{check_out_date.strftime('%Y/%m/%d')}\n"
      f"晚數：{nights}\n"
      f"總金額：{total_price}\n"
      f"備註：{booking_info.notes}\n"
      f"來源：{booking_info.source}\n"
      f"訂金：{prepayment}元/{booking_info.prepayment_status}\n"
      f"預計讓他睡：{booking_info.room_ids}"
    )

  return message

# Function to determine if a customer name is generic
def is_generic_name(name):
  for g_name in GENERIC_NAMES:
    if g_name in name:
      return True
  return False
