import os
import logging
import datetime
from linebot import LineBotApi
from linebot.models import TextSendMessage
from const import db_config
from utils.data_access.booking_dao import BookingDAO
from utils.line_messaging_utils import generate_booking_carousel_message

# Task to load latest bookings and sync to Google Calendar
def notify_daily_bookings():
  booking_dao = BookingDAO.get_instance(db_config, logging)
  date_today = datetime.date.today()
  messages = []
  bookings_all = booking_dao.search_booking_by_date(date_today.strftime('%Y-%m-%d'))

  if not bookings_all:
    messages.append(TextSendMessage(text="今日無訂單"))
    logging.info("No bookings today.")

  else:
    bookings_check_in = booking_dao.search_booking_by_date(date_today.strftime('%Y-%m-%d'), mode='check_in_date')
    bookings_check_in_ids = { bi.booking_id for bi in bookings_check_in }
    bookings_cont = [booking_info for booking_info in bookings_all if booking_info.booking_id not in bookings_check_in_ids]
    bookings_cont_ids = { bi.booking_id for bi in bookings_cont }

    if bookings_check_in:
      messages.append(TextSendMessage(text="今日入住："))
      messages.append(generate_booking_carousel_message(bookings_check_in))

    if bookings_cont:
      messages.append(TextSendMessage(text="今日續住："))
      messages.append(generate_booking_carousel_message(bookings_cont))

    logging.info(f"Notifying daily bookings. Check-ins: {bookings_check_in_ids}, Cont: {bookings_cont_ids}")

  line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
  recipient_id = os.getenv('LINE_BROADCAST_GROUP_ID')

  for message in messages:
    line_bot_api.push_message(
      recipient_id,
      message
    )
