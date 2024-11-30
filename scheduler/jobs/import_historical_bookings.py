import os
import re
import logging
from datetime import datetime, timedelta
from const import db_config
from const.booking_const import VALID_BOOKING_SOURCES
from utils.data_access.data_class.booking_info import BookingInfo
from utils.data_access.booking_dao import BookingDAO
from utils.input_utils import format_phone_number

# DB Connection details
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Example booking text block
SORTED_BOOKINGS_FILE_PATH = './data/sorted_bookings.txt'

# Function to parse the booking text block
def parse_booking(text):
  try:
    booking_data = {}

    # Check if the booking is canceled
    if '[取消]' in text:
      booking_data['status'] = 'canceled'
    else:
      booking_data['status'] = 'new'  # Default to 'new' unless specified otherwise

    # Using regular expressions to extract key fields
    booking_data['booking_id'] = int(re.search(r'ＩＤ：(\d+)', text).group(1))
    booking_data['customer_name'] = re.search(r'姓名：(.+)', text).group(1)

    # Extract phone_number (starts with + and followed by digits or may start with 0 for Taiwan format)
    phone_match = re.search(r'電話：(\+?\d+)', text)
    if phone_match:
      phone_number = phone_match.group(1)
      booking_data['phone_number'] = format_phone_number(phone_number)

    booking_data['room_name_string'] = re.search(r'預計讓他睡：(.+)', text).group(1)  # This will be processed later to extract rooms
    booking_data['check_in_date'] = re.search(r'入住日期：(\d{4}/\d{2}/\d{2})', text).group(1)
    check_out_date = re.search(r'退房日期：(\d{4}/\d{2}/\d{2})', text).group(1)
    booking_data['last_date'] = (datetime.strptime(check_out_date, '%Y/%m/%d') - timedelta(days=1)).strftime('%Y/%m/%d')
    booking_data['total_price'] = float(re.search(r'總金額：(\d+)', text).group(1))
    booking_data['source'] = re.search(r'來源：(.+)', text).group(1).replace('_', '.')

    if (booking_data['source'] == 'Booking.com'):
      booking_data['source'] = 'Booking_com'

    # Parse the prepayment and status from the "訂金" line
    prepayment_info = re.search(r'訂金：(\d+)元/(.+)', text)
    booking_data['prepayment'] = float(prepayment_info.group(1))
    booking_data['prepayment_status'] = 'unpaid'
    prepayment_status = prepayment_info.group(2)
    if prepayment_status == '已付':
      booking_data['prepayment_status'] = 'paid'
      if booking_data['status'] == 'new':
        booking_data['status'] = 'prepaid'

    booking_data['notes'] = re.search(r'備註：(.*)', text).group(1)

    return booking_data
  except Exception as e:
    logging.error(f"Error parsing text: {text}\n Error: {e}")
    return None

# Function to do sanity check on the booking field values. Print error if any invalid field found
def validate_booking(booking_data):
  if (booking_data['booking_id'] <= 0):
    logging.warning(f"[Validation Warning] Invalid booking_id: {booking_data['booking_id']}")
  if (len(booking_data['customer_name']) <= 0):
    logging.warning(f"[Validation Warning] #{booking_data['booking_id']} with no customer name")
  if (len(booking_data['phone_number']) <= 0):
    logging.warning(f"[Validation Warning] #{booking_data['booking_id']} with no phone number")
  if (len(booking_data['room_name_string']) <= 0):
    logging.warning(f"[Validation Warning] #{booking_data['booking_id']} with no room specified")
  if (len(booking_data['check_in_date']) <= 0):
    logging.warning(f"[Validation Warning] #{booking_data['booking_id']} with no check_in_date")
  if (len(booking_data['last_date']) <= 0):
    logging.warning(f"[Validation Warning] #{booking_data['booking_id']} with no last_date")
  if (booking_data['total_price'] <= 0):
    logging.warning(f"[Validation Warning] #{booking_data['booking_id']} with total_price <= 0")
  if (booking_data['source'] not in VALID_BOOKING_SOURCES):
    logging.warning(f"[Validation Warning] #{booking_data['booking_id']} with invalid source: {booking_data['source']}")

# Function to extract associated room_ids from room_name_string
def extract_room_ids(available_room_ids, room_name_string):
  room_ids = []
  # Match each character in room_name_string to an available room_id
  for char in room_name_string:
    if char in available_room_ids:
      room_ids.append(char)
  return room_ids

def import_historical_bookings():
  booking_dao = BookingDAO.get_instance(db_config, logging)
  all_room_ids = booking_dao.get_all_room_ids()

  if not all_room_ids:
    logging.warning(f"Failed to load available Room IDs. Aborted")
    return

  with open(SORTED_BOOKINGS_FILE_PATH, 'r', encoding='utf-8') as f:
    content = f.read()
    booking_text_list = content.split("\n\n")
    for booking_text in booking_text_list:
      if (not booking_text):
        continue
      booking_data = parse_booking(booking_text)
      if (not booking_data):
        continue
      validate_booking(booking_data)
      booking_info = BookingInfo(
        booking_id=booking_data['booking_id'],
        status=booking_data['status'],
        customer_name=booking_data['customer_name'],
        phone_number=booking_data['phone_number'],
        check_in_date=booking_data['check_in_date'],
        last_date=booking_data['last_date'],
        total_price=booking_data['total_price'],
        notes=booking_data['notes'],
        source=booking_data['source'],
        prepayment=booking_data['prepayment'],
        prepayment_note='',
        prepayment_status=booking_data['prepayment_status'],
        room_ids=extract_room_ids(all_room_ids, booking_data['room_name_string'])
      )
      booking_id = booking_dao.upsert_booking(booking_info)
      logging.info(f"Booking #{booking_id} imported successfully")
