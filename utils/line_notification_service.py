import os
from urllib.parse import quote
from linebot import LineBotApi
from linebot.models import TextSendMessage
from const import line_config, property_config
from const.notification_templates import ASK_FOR_PREPAYMENT
from utils.data_access.data_class.booking_info import BookingInfo
from utils.booking_utils import format_booking_info, get_booking_room_brief
from utils.input_utils import format_phone_number_for_display

class LineNotificationService:
  def __init__(self, logger):
    self.line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
    self.recipient_id = os.getenv('LINE_BROADCAST_GROUP_ID')
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

  def notify_public_booking_created_admins(self, booking_info: BookingInfo, room_type_summary: dict):
    if not line_config.LINE_ADMIN_USER_IDS:
      self.logger.info(f"No LINE admin recipients configured. booking_id: {booking_info.booking_id}")
      return
    if not booking_info.prepayment or booking_info.prepayment_status != 'unpaid':
      self.logger.info(f"Skipping admin SMS notification because booking does not need unpaid prepayment. booking_id: {booking_info.booking_id}")
      return

    try:
      nights = (booking_info.last_date - booking_info.check_in_date).days + 1
      room_brief = get_booking_room_brief(room_type_summary, booking_info.extra_bed_count)
      sms_body = ASK_FOR_PREPAYMENT.format(
        property_name=property_config.PROPERTY_NAME,
        check_in_date=booking_info.check_in_date.strftime('%m/%d'),
        nights=nights,
        room_brief=room_brief,
        total_price=int(booking_info.total_price),
        prepayment=int(booking_info.prepayment),
        bank_account_info=property_config.BANK_ACCOUNT_INFO
      ).strip()
      sms_body = (
        f"訂單編號：{booking_info.booking_id}\n"
        f"{sms_body}\n\n"
      )
      sms_url = f"sms:{format_phone_number_for_display(booking_info.phone_number)}?body={quote(sms_body)}"
      messages = [
        TextSendMessage(text=f"官網訂單已建立，請發送訂金簡訊：\n\n{format_booking_info(booking_info)}"),
        TextSendMessage(text=f"匯款訊息：\n\n{sms_body}"),
        TextSendMessage(text=f"發送簡訊：\n\n{sms_url}"),
      ]
      for admin_user_id in line_config.LINE_ADMIN_USER_IDS:
        self.line_bot_api.push_message(admin_user_id, messages)
      self.logger.info(f"Public booking admin SMS notification sent. booking_id: {booking_info.booking_id}. recipients: {len(line_config.LINE_ADMIN_USER_IDS)}")
    except Exception as e:
      self.logger.info(f"Failed to send public booking admin SMS notification. booking_id: {booking_info.booking_id}. error: {e}")

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

  def notify_booking_restored(self, booking_info: BookingInfo):
    try:
      message = format_booking_info(booking_info, custom_status_mark='[復原]')
      self.line_bot_api.push_message(
        self.recipient_id,
        TextSendMessage(text=message)
      )
      self.logger.info(f"Booking restored notification sent to group {self.recipient_id}. booking_id: {booking_info.booking_id}")
    except Exception as e:
      self.logger.info(f"Failed to send booking restored notification to group {self.recipient_id}. booking_id: {booking_info.booking_id}. error: {e}")

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
      message = f"{booking_info.check_in_date.strftime('%m/%d')} ID{booking_info.booking_id} {booking_info.customer_name} 已付訂金{int(booking_info.prepayment)}元 摘要\"{booking_info.prepayment_note}\""
      self.line_bot_api.push_message(
        self.recipient_id,
        TextSendMessage(text=message)
      )
      self.logger.info(f"Booking prepaid notification sent to group {self.recipient_id}. booking_id: {booking_info.booking_id}")
    except Exception as e:
      self.logger.info(f"Failed to send booking prepaid notification to group {self.recipient_id}. booking_id: {booking_info.booking_id}. error: {e}")
