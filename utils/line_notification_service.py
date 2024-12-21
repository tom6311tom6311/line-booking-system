import os
from linebot import LineBotApi
from linebot.models import TextSendMessage
from utils.data_access.data_class.booking_info import BookingInfo
from utils.booking_utils import format_booking_info

class LineNotificationService:
  def __init__(self, logger):
    self.line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
    self.recipient_id = os.getenv('LINE_NOTIFICATION_GROUP_ID')
    self.logger = logger

  def notify_booking_created(self, booking_info: BookingInfo):
    try:
      message = format_booking_info(booking_info)
      self.line_bot_api.push_message(
        self.recipient_id,
        TextSendMessage(text=message)
      )
      self.logger.info(f"Booking created notification sent to group {self.recipient_id}. booking_id: {booking_info.booking_id}")
    except Exception as e:
      self.logger.info(f"Failed to send booking created notification to group {self.recipient_id}. booking_id: {booking_info.booking_id}. error: {e}")

  def notify_booking_updated(self, booking_info: BookingInfo):
    try:
      message = format_booking_info(booking_info, custom_status_mark='[更改]')
      self.line_bot_api.push_message(
        self.recipient_id,
        TextSendMessage(text=message)
      )
      self.logger.info(f"Booking updated notification sent to group {self.recipient_id}. booking_id: {booking_info.booking_id}")
    except Exception as e:
      self.logger.info(f"Failed to send booking updated notification to group {self.recipient_id}. booking_id: {booking_info.booking_id}. error: {e}")

  def notify_booking_canceled(self, booking_info: BookingInfo):
    try:
      message = f"{booking_info.check_in_date.strftime('%m/%d')} ID{booking_info.booking_id} {booking_info.customer_name} 取消"
      self.line_bot_api.push_message(
        self.recipient_id,
        TextSendMessage(text=message)
      )
      self.logger.info(f"Booking canceled notification sent to group {self.recipient_id}. booking_id: {booking_info.booking_id}")
    except Exception as e:
      self.logger.info(f"Failed to send booking canceled notification to group {self.recipient_id}. booking_id: {booking_info.booking_id}. error: {e}")

  def notify_booking_prepaid(self, booking_info: BookingInfo):
    try:
      message = f"{booking_info.check_in_date.strftime('%m/%d')} ID{booking_info.booking_id} {booking_info.customer_name} 已付訂金{booking_info.prepayment}元 摘要{booking_info.prepayment_note}"
      self.line_bot_api.push_message(
        self.recipient_id,
        TextSendMessage(text=message)
      )
      self.logger.info(f"Booking prepaid notification sent to group {self.recipient_id}. booking_id: {booking_info.booking_id}")
    except Exception as e:
      self.logger.info(f"Failed to send booking prepaid notification to group {self.recipient_id}. booking_id: {booking_info.booking_id}. error: {e}")
