import datetime
import typing
from const.booking_const import GENERIC_NAMES, BOOKING_STATUS_MARK, PREPAYMENT_STATUS_MAP, GENERIC_PHONE_NUMBER_POSTFIX
from utils.data_access.data_class.booking_info import BookingInfo

# Function to format the booking info as per the required format
def format_booking_info(booking_info: typing.Optional[BookingInfo]=None, variant='normal', custom_status_mark='', custom_postfix=''):
  if not booking_info:
    return None

  phone_number = booking_info.phone_number
  if phone_number.startswith('+886'):
    phone_number = '0' + phone_number[4:]
  total_price = int(booking_info.total_price)
  prepayment = int(booking_info.prepayment)

  status_mark = custom_status_mark
  if not status_mark:
    status_mark = BOOKING_STATUS_MARK[booking_info.status] if booking_info.status in BOOKING_STATUS_MARK else ''

  # Calculate the number of nights
  nights = (booking_info.last_date - booking_info.check_in_date).days + 1
  check_out_date = booking_info.last_date + datetime.timedelta(days=1)

  prepayment_status = PREPAYMENT_STATUS_MAP[booking_info.prepayment_status]

  # Format the response message
  message = ""
  if variant == 'carousel':
    message = (
      f"電話：{phone_number}\n"
      f"入住：{booking_info.check_in_date.strftime('%m/%d')}\n"
      f"晚數：{nights}\n"
      f"訂金：{prepayment}元/{prepayment_status}\n"
    )
  elif variant == 'calendar':
    message = (
      f"ＩＤ：{booking_info.booking_id}\n"
      f"電話：{phone_number}\n"
      f"訂金：{prepayment}元/{prepayment_status}\n"
      f"來源：{booking_info.source}\n"
      f"備註：{booking_info.notes}\n"
    )
  elif variant == 'report':
    message = (
      f"[訂單]\n"
      f"ＩＤ：{booking_info.booking_id if booking_info.booking_id > 0 else ''}\n"
      f"姓名：{booking_info.customer_name}\n"
      f"入住日期：{booking_info.check_in_date.strftime('%Y/%m/%d')}\n"
      f"晚數：{nights}\n"
      f"來源：{booking_info.source}\n"
      f"房間：{booking_info.room_ids}\n"
      f"總金額：{total_price}\n"
      f"{custom_postfix}"
    )
  else:
    message = (
      f"[訂單]{status_mark}\n"
      f"ＩＤ：{booking_info.booking_id if booking_info.booking_id > 0 else ''}\n"
      f"姓名：{booking_info.customer_name}\n"
      f"電話：{phone_number}\n"
      f"入住日期：{booking_info.check_in_date.strftime('%Y/%m/%d')}\n"
      f"退房日期：{check_out_date.strftime('%Y/%m/%d')}\n"
      f"晚數：{nights}\n"
      f"總金額：{total_price}\n"
      f"備註：{booking_info.notes}\n"
      f"來源：{booking_info.source}\n"
      f"訂金：{prepayment}元/{prepayment_status}\n"
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
  if ('prepayment_status' in booking_dict and booking_dict['prepayment_status'] == booking_info.prepayment_status):
    del booking_dict['prepayment_status']
  if ('prepayment_note' in booking_dict and booking_dict['prepayment_note'] == booking_info.prepayment_note):
    del booking_dict['prepayment_note']
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
  if ('prepayment_status' in booking_dict):
    message += f"訂金狀態：{'未付' if booking_dict['prepayment_status'] == 'unpaid' else '已付'}\n"
  if ('prepayment_note' in booking_dict):
    message += f"訂金匯款摘要：{booking_dict['prepayment_note']}\n"
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

# Function to determine if a phone number is generic
def is_generic_phone_number(phone_number):
  return phone_number.endswith(GENERIC_PHONE_NUMBER_POSTFIX)

def get_prepayment_estimation(total_price):
  return int(int(total_price) * 0.3 // 100 * 100)

def generate_report(year_month: str, bookings: list[BookingInfo]):
  message = (
    f"##### {year_month}月報表  #####\n\n"
    f"------------------------------\n\n"
  )

  total_revenue = 0
  total_amount_for_booking_com = 0
  total_amount_for_staff = 0
  total_amount_left = 0
  for booking_info in bookings:
    amount_for_booking_com = int(booking_info.total_price * .12) if booking_info.source == 'Booking_com' else 0
    amount_for_staff = int((booking_info.total_price - amount_for_booking_com) * .2)
    amount_left = int(booking_info.total_price - amount_for_booking_com - amount_for_staff * 2)

    total_revenue += int(booking_info.total_price)
    total_amount_for_booking_com += amount_for_booking_com
    total_amount_for_staff += amount_for_staff
    total_amount_left += amount_left

    financial_result_text = (
      f"Booking_com佣金：{amount_for_booking_com}\n"
      f"給姑姑：{amount_for_staff}\n"
      f"給雅雯：{amount_for_staff}\n"
      f"結餘：{amount_left}\n"
    )

    message += format_booking_info(booking_info, 'report', custom_postfix=financial_result_text)
    message += '\n'
  message += f"------------------------------\n\n"
  message += f"[總結]\n"

  message += (
    f"營業額：{total_revenue}\n"
    f"Booking_com佣金：{total_amount_for_booking_com}\n"
    f"給姑姑：{total_amount_for_staff}\n"
    f"給雅雯：{total_amount_for_staff}\n"
    f"結餘：{total_amount_left}"
  )

  return message
