from datetime import datetime, timedelta

from flask import jsonify, request

from const.booking_const import EXTRA_BED_PRICE_PER_NIGHT
from utils.input_utils import format_phone_number, is_valid_date, is_valid_phone_number


def api_error(message, status_code=400):
  return jsonify({ 'error': message }), status_code


def parse_api_json():
  payload = request.get_json(silent=True)
  return payload if isinstance(payload, dict) else {}


def parse_date_value(value, field_name):
  if not value or not is_valid_date(value):
    raise ValueError(f"{field_name} must be YYYY-MM-DD")
  return datetime.strptime(value, '%Y-%m-%d').date()


def parse_date_range(source):
  check_in = parse_date_value(source.get('checkIn'), 'checkIn')
  check_out = parse_date_value(source.get('checkOut'), 'checkOut')
  nights = (check_out - check_in).days
  if nights < 1 or nights > 15:
    raise ValueError("checkOut must be 1 to 15 nights after checkIn")
  return check_in, check_out, check_out - timedelta(days=1), nights


def normalize_api_phone_number(phone_number):
  if not phone_number or not is_valid_phone_number(phone_number):
    raise ValueError("phoneNumber is invalid")
  return format_phone_number(phone_number)


def serialize_room(room, is_available=None):
  serialized = {
    'roomId': room['room_id'],
    'name': room['room_name'],
    'roomType': room['room_type'],
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


def serialize_booking(booking_info):
  check_out = booking_info.last_date + timedelta(days=1)
  return {
    'bookingId': booking_info.booking_id,
    'status': booking_info.status,
    'customerName': booking_info.customer_name,
    'phoneNumber': booking_info.phone_number,
    'checkIn': booking_info.check_in_date.isoformat(),
    'checkOut': check_out.isoformat(),
    'nights': (check_out - booking_info.check_in_date).days,
    'roomIds': list(booking_info.room_ids),
    'extraBedCount': booking_info.extra_bed_count,
    'extraBedCounts': booking_info.extra_bed_counts,
    'totalPrice': int(booking_info.total_price),
    'prepayment': int(booking_info.prepayment),
    'prepaymentStatus': booking_info.prepayment_status,
    'source': booking_info.source,
    'notes': booking_info.notes,
  }


def get_rooms_by_id(booking_dao):
  rooms = booking_dao.get_rooms_by_ids()
  return { room['room_id']: room for room in rooms }


def validate_public_room_ids(room_ids, booking_dao):
  if not isinstance(room_ids, list) or not room_ids:
    raise ValueError("roomIds must be a non-empty list")
  if not all(isinstance(room_id, str) for room_id in room_ids):
    raise ValueError("roomIds must contain strings")
  duplicate_room_ids = { room_id for room_id in room_ids if room_ids.count(room_id) > 1 }
  if duplicate_room_ids:
    raise ValueError("roomIds must not contain duplicates")

  rooms = get_rooms_by_id(booking_dao)
  invalid_room_ids = [room_id for room_id in room_ids if room_id not in rooms]
  if invalid_room_ids:
    raise ValueError(f"Unsupported roomIds: {', '.join(invalid_room_ids)}")

  closed_room_ids = [room_id for room_id in room_ids if rooms[room_id]['room_status'] != 'available']
  if closed_room_ids:
    raise ValueError(f"Closed roomIds: {', '.join(closed_room_ids)}")
  return room_ids


def parse_extra_bed_counts(value, room_ids, booking_dao):
  if value is None:
    return {room_id: 0 for room_id in room_ids}
  if not isinstance(value, dict):
    raise ValueError("extraBedCounts must be an object keyed by roomId")

  rooms_by_id = get_rooms_by_id(booking_dao)
  extra_bed_counts = {}
  invalid_room_ids = [room_id for room_id in value if room_id not in room_ids]
  if invalid_room_ids:
    raise ValueError(f"extraBedCounts contains unselected roomIds: {', '.join(invalid_room_ids)}")

  for room_id in room_ids:
    raw_count = value.get(room_id, 0)
    if isinstance(raw_count, bool):
      raise ValueError(f"extraBedCounts.{room_id} must be an integer")
    try:
      extra_bed_count = int(raw_count)
    except (TypeError, ValueError):
      raise ValueError(f"extraBedCounts.{room_id} must be an integer")

    max_extra_bed_count = rooms_by_id[room_id]['extra_bed_number']
    if extra_bed_count < 0 or extra_bed_count > max_extra_bed_count:
      raise ValueError(f"extraBedCounts.{room_id} must be between 0 and {max_extra_bed_count}")
    extra_bed_counts[room_id] = extra_bed_count
  return extra_bed_counts


def ensure_rooms_available(room_ids, check_in_date, last_date, booking_dao, exclude_booking_id=None):
  available_room_ids = booking_dao.get_available_room_ids(check_in_date, last_date, exclude_booking_id) or []
  unavailable_room_ids = [room_id for room_id in room_ids if room_id not in available_room_ids]
  if unavailable_room_ids:
    raise ValueError(f"Unavailable roomIds: {', '.join(unavailable_room_ids)}")


def get_owned_booking_or_error(booking_id, phone_number, booking_dao):
  booking_info = booking_dao.get_booking_info(booking_id)
  normalized_phone_number = normalize_api_phone_number(phone_number)
  if not booking_info or booking_info.phone_number != normalized_phone_number:
    return None
  return booking_info
