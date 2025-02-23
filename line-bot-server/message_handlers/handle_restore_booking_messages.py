from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction
from const import line_config
from utils.data_access.booking_dao import BookingDAO

def handle_restore_booking_messages(user_message: str, session: dict, booking_dao: BookingDAO):
  reply_messages = []
  if user_message == line_config.USER_COMMAND_RESTORE_BOOKING__CANCEL:
    # clear session data
    session['flow'], session['step'], session['data'] = None, None, {}
    reply_messages.append(TextSendMessage(text="好的，沒有復原"))

  elif user_message == line_config.USER_COMMAND_RESTORE_BOOKING__CONFIRM:
    success = booking_dao.restore_booking(session['data']['booking_id'])
    reply_messages.append(TextSendMessage(text=("已復原訂單，請注意該日房間是否重複" if success else "復原訂單時遇到錯誤")))
    session['flow'], session['step'], session['data'] = None, None, {}

  else:
    quick_reply_buttons = [
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_RESTORE_BOOKING__CANCEL,
        text=line_config.USER_COMMAND_RESTORE_BOOKING__CANCEL)
      ),
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_RESTORE_BOOKING__CONFIRM,
        text=line_config.USER_COMMAND_RESTORE_BOOKING__CONFIRM)
      ),
    ]
    reply_messages.append(TextSendMessage(text=f"是否復原訂單 #{session['data']['booking_id']}？", quick_reply=QuickReply(items=quick_reply_buttons)))
  return reply_messages
