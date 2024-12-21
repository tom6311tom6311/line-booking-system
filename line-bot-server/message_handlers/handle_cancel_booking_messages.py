from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction
from app_const import line_config
from utils.data_access.booking_dao import BookingDAO

def handle_cancel_booking_messages(user_message: str, session: dict, booking_dao: BookingDAO):
  reply_messages = []
  if user_message == line_config.USER_COMMAND_CANCEL_BOOKING__CANCEL:
    # clear session data
    session['flow'], session['step'], session['data'] = None, None, {}
    reply_messages.append(TextSendMessage(text="好的，沒有取消"))

  elif user_message == line_config.USER_COMMAND_CANCEL_BOOKING__CONFIRM:
    success = booking_dao.cancel_booking(session['data']['booking_id'])
    reply_messages.append(TextSendMessage(text=("已取消訂單" if success else "取消訂單時遇到錯誤")))
    session['flow'], session['step'], session['data'] = None, None, {}

  else:
    quick_reply_buttons = [
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_CANCEL_BOOKING__CANCEL,
        text=line_config.USER_COMMAND_CANCEL_BOOKING__CANCEL)
      ),
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_CANCEL_BOOKING__CONFIRM,
        text=line_config.USER_COMMAND_CANCEL_BOOKING__CONFIRM)
      ),
    ]
    reply_messages.append(TextSendMessage(text=f"是否取消訂單 #{session['data']['booking_id']}？", quick_reply=QuickReply(items=quick_reply_buttons)))
  return reply_messages
