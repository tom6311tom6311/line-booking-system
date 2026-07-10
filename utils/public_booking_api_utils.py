import os
import re
from datetime import datetime, timedelta

from flask import jsonify, request

from const.booking_const import EXTRA_BED_PRICE_PER_NIGHT, PUBLIC_BOOKING_SOURCE, ROOM_TYPES
from utils.datetime_utils import get_local_today
from utils.input_utils import format_phone_number, format_phone_number_for_display, is_valid_date, is_valid_phone_number

ROOM_TYPE_LABELS = { room_type: room_type_name for room_type, room_type_name, _ in ROOM_TYPES }
MIN_CANCEL_DAYS_BEFORE_CHECK_IN = 7
GENERIC_PUBLIC_API_ERROR_MESSAGE = "系統暫時無法處理，請稍後再試。"


def get_public_booking_discount_per_room_night():
  try:
    return max(0, int(os.getenv('PUBLIC_BOOKING_DISCOUNT_PER_ROOM_NIGHT', '0') or 0))
  except ValueError:
    return 0


def calculate_public_booking_discount(room_ids, nights):
  return get_public_booking_discount_per_room_night() * len(room_ids) * nights


def apply_public_booking_discount(total_price, room_ids, nights):
  discount_amount = min(int(total_price), calculate_public_booking_discount(room_ids, nights))
  return int(total_price) - discount_amount, discount_amount


def api_error(message, status_code=400):
  if not isinstance(message, str) or not re.search(r'[\u3400-\u9fff]', message):
    message = GENERIC_PUBLIC_API_ERROR_MESSAGE
  return jsonify({ 'error': message }), status_code


def parse_api_json():
  payload = request.get_json(silent=True)
  return payload if isinstance(payload, dict) else {}


def parse_date_value(value, field_name):
  if not value or not is_valid_date(value):
    raise ValueError("日期格式不正確，請使用像 2026-07-10 這樣的格式。")
  return datetime.strptime(value, '%Y-%m-%d').date()


def parse_date_range(source):
  check_in = parse_date_value(source.get('checkIn'), 'checkIn')
  check_out = parse_date_value(source.get('checkOut'), 'checkOut')
  if check_in < get_local_today():
    raise ValueError("入住日期不能早於今天")
  nights = (check_out - check_in).days
  if nights < 1 or nights > 15:
    raise ValueError("退房日期需晚於入住日期，且住宿晚數不可超過 15 晚。")
  return check_in, check_out, check_out - timedelta(days=1), nights


def normalize_api_phone_number(phone_number):
  if not phone_number or not is_valid_phone_number(phone_number):
    raise ValueError("電話格式不正確，請輸入 09 開頭的 10 碼手機號碼。")
  return format_phone_number(phone_number)


def serialize_room(room, is_available=None):
  serialized = {
    'roomId': room['room_id'],
    'name': room['room_name'],
    'roomType': room['room_type'],
    'roomTypeLabel': ROOM_TYPE_LABELS.get(room['room_type'], room['room_type']),
    'capacity': room['capacity'],
    'holidayPricePerNight': room['holiday_price_per_night'],
    'weekdayPricePerNight': room['weekday_price_per_night'],
    'extraBedNumber': room['extra_bed_number'],
    'extraBedPricePerNight': EXTRA_BED_PRICE_PER_NIGHT,
    'description': room['description'],
    'status': room['room_status'],
  }
  if is_available is not None:
    serialized['available'] = is_available
  return serialized


def serialize_booking(booking_info, website_discount_amount=0, booking_dao=None):
  check_out = booking_info.last_date + timedelta(days=1)
  nights = (check_out - booking_info.check_in_date).days
  if not website_discount_amount and booking_info.source == PUBLIC_BOOKING_SOURCE:
    website_discount_amount = calculate_public_booking_discount(list(booking_info.room_ids), nights)
  website_discount_amount = int(website_discount_amount or 0)
  original_total_price = int(booking_info.total_price) + website_discount_amount
  serialized = {
    'bookingId': booking_info.booking_id,
    'status': booking_info.status,
    'customerName': booking_info.customer_name,
    'phoneNumber': format_phone_number_for_display(booking_info.phone_number),
    'checkIn': booking_info.check_in_date.isoformat(),
    'checkOut': check_out.isoformat(),
    'nights': nights,
    'roomIds': list(booking_info.room_ids),
    'extraBedCount': booking_info.extra_bed_count,
    'extraBedCounts': booking_info.extra_bed_counts,
    'originalTotalPrice': original_total_price,
    'websiteDiscountAmount': website_discount_amount,
    'totalPrice': int(booking_info.total_price),
    'prepayment': int(booking_info.prepayment),
    'prepaymentStatus': booking_info.prepayment_status,
    'source': booking_info.source,
    'notes': booking_info.notes,
  }
  if booking_dao:
    rooms_by_id = {
      room['room_id']: room
      for room in booking_dao.get_rooms_by_ids(list(booking_info.room_ids))
    }
    serialized['rooms'] = [
      serialize_room(rooms_by_id[room_id])
      for room_id in booking_info.room_ids
      if room_id in rooms_by_id
    ]
  return serialized


def get_rooms_by_id(booking_dao):
  rooms = booking_dao.get_rooms_by_ids()
  return { room['room_id']: room for room in rooms }


def validate_public_room_ids(room_ids, booking_dao):
  if not isinstance(room_ids, list) or not room_ids:
    raise ValueError("請至少選擇一間房間。")
  if not all(isinstance(room_id, str) for room_id in room_ids):
    raise ValueError("房間資料格式不正確，請重新選擇房間。")
  duplicate_room_ids = { room_id for room_id in room_ids if room_ids.count(room_id) > 1 }
  if duplicate_room_ids:
    raise ValueError("房間不可重複選擇，請重新確認。")

  rooms = get_rooms_by_id(booking_dao)
  invalid_room_ids = [room_id for room_id in room_ids if room_id not in rooms]
  if invalid_room_ids:
    raise ValueError("選擇的房間不存在，請重新查詢。")

  closed_room_ids = [room_id for room_id in room_ids if rooms[room_id]['room_status'] != 'available']
  if closed_room_ids:
    raise ValueError("選擇的房間目前未開放訂房，請重新選擇。")
  return room_ids


def parse_extra_bed_counts(value, room_ids, booking_dao):
  if value is None:
    return {room_id: 0 for room_id in room_ids}
  if not isinstance(value, dict):
    raise ValueError("加床資料格式不正確，請重新選擇加床數。")

  rooms_by_id = get_rooms_by_id(booking_dao)
  extra_bed_counts = {}
  invalid_room_ids = [room_id for room_id in value if room_id not in room_ids]
  if invalid_room_ids:
    raise ValueError("加床資料包含未選擇的房間，請重新確認。")

  for room_id in room_ids:
    raw_count = value.get(room_id, 0)
    if isinstance(raw_count, bool):
      raise ValueError("加床數需為整數。")
    try:
      extra_bed_count = int(raw_count)
    except (TypeError, ValueError):
      raise ValueError("加床數需為整數。")

    max_extra_bed_count = rooms_by_id[room_id]['extra_bed_number']
    if extra_bed_count < 0 or extra_bed_count > max_extra_bed_count:
      raise ValueError(f"加床數需介於 0 到 {max_extra_bed_count} 床之間。")
    extra_bed_counts[room_id] = extra_bed_count
  return extra_bed_counts


def ensure_rooms_available(room_ids, check_in_date, last_date, booking_dao, exclude_booking_id=None):
  available_room_ids = booking_dao.get_available_room_ids(check_in_date, last_date, exclude_booking_id) or []
  unavailable_room_ids = [room_id for room_id in room_ids if room_id not in available_room_ids]
  if unavailable_room_ids:
    raise ValueError("選擇的房間已被預訂，請重新查詢空房。")


def get_owned_booking_or_error(booking_id, phone_number, booking_dao):
  booking_info = booking_dao.get_booking_info(booking_id)
  normalized_phone_number = normalize_api_phone_number(phone_number)
  if not booking_info or booking_info.phone_number != normalized_phone_number:
    return None
  return booking_info


def can_cancel_public_booking(booking_info):
  return (booking_info.check_in_date - get_local_today()).days >= MIN_CANCEL_DAYS_BEFORE_CHECK_IN
