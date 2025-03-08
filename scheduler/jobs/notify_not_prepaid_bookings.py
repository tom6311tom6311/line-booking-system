import os
import logging
from linebot import LineBotApi
from linebot.models import TextSendMessage
from const import db_config
from utils.data_access.booking_dao import BookingDAO
from utils.line_messaging_utils import generate_booking_carousel_message

# Task to load latest bookings and sync to Google Calendar
def notify_not_prepaid_bookings():
  booking_dao = BookingDAO.get_instance(db_config, logging)
  messages = []
  bookings = booking_dao.search_booking_not_prepaid()

  if not bookings:
    messages.append(TextSendMessage(text="所有訂單都已經付訂金囉！"))
    logging.info("No not prepaid bookings.")

  else:
    messages.append(TextSendMessage(text="未付訂金："))
    messages.append(generate_booking_carousel_message(bookings))
    bookings_ids = { b.booking_id for b in bookings }
    logging.info(f"Notifying not prepaid bookings. Booking_ids: {bookings_ids}")

  line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
  recipient_id = os.getenv('LINE_BROADCAST_GROUP_ID')

  for message in messages:
    line_bot_api.push_message(
      recipient_id,
      message
    )
