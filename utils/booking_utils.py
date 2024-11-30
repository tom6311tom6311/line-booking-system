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
      f"ＩＤ：{booking_info.booking_id if booking_info.booking_id > 0 else ''}\n"
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


# Trim the booking changes dict by removing values that does not actually change
def trim_booking_changes(booking_dict: dict, booking_info: BookingInfo):
  if ('customer_name' in booking_dict and booking_dict['customer_name'] == booking_info.customer_name):
    del booking_dict['customer_name']
  if ('phone_number' in booking_dict and booking_dict['phone_number'] == booking_info.phone_number):
    del booking_dict['phone_number']
  if ('check_in_date' in booking_dict and booking_dict['check_in_date'] == booking_info.check_in_date):
    del booking_dict['check_in_date']
  if ('last_date' in booking_dict and booking_dict['last_date'] == booking_info.last_date):
    del booking_dict['last_date']
  if ('total_price' in booking_dict and booking_dict['total_price'] == booking_info.total_price):
    del booking_dict['total_price']
  if ('notes' in booking_dict and booking_dict['notes'] == booking_info.notes):
    del booking_dict['notes']
  if ('source' in booking_dict and booking_dict['source'] == booking_info.source):
    del booking_dict['source']
  if ('prepayment' in booking_dict and booking_dict['prepayment'] == booking_info.prepayment):
    del booking_dict['prepayment']
  if ('room_ids' in booking_dict and ''.join(booking_dict['room_ids']) == booking_info.customer_name):
    del booking_dict['room_ids']

  return booking_dict

# Function to list down the changes of a booking
def format_booking_changes(booking_dict: dict):
  message = "更改項目：\n"
  if ('customer_name' in booking_dict):
    message += f"姓名：{booking_dict['customer_name']}\n"
  if ('phone_number' in booking_dict):
    if booking_dict['phone_number'].startswith('+886'):
      phone_number = '0' + booking_dict['phone_number'][4:]
    message += f"電話：{phone_number}\n"
  if ('check_in_date' in booking_dict):
    message += f"入住日期：{booking_dict['check_in_date'].strftime('%Y/%m/%d')}\n"
  if ('last_date' in booking_dict):
    check_out_date = booking_dict['last_date'] + datetime.timedelta(days=1)
    message += f"退房日期：{check_out_date.strftime('%Y/%m/%d')}\n"
  if ('total_price' in booking_dict):
    message += f"總金額：{booking_dict['total_price']}\n"
  if ('notes' in booking_dict):
    message += f"備註：{booking_dict['notes']}\n"
  if ('source' in booking_dict):
    message += f"來源：{booking_dict['source']}\n"
  if ('prepayment' in booking_dict):
    message += f"訂金：{booking_dict['prepayment']}元\n"
  if ('room_ids' in booking_dict):
    message += f"預計讓他睡：{''.join(booking_dict['room_ids'])}\n"

  if message == "更改項目：\n":
    return None
  return message

# Function to determine if a customer name is generic
def is_generic_name(name):
  for g_name in GENERIC_NAMES:
    if g_name in name:
      return True
  return False
