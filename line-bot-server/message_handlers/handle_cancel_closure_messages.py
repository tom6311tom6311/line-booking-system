from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction
from const import line_config
from utils.data_access.booking_dao import BookingDAO

def handle_cancel_closure_messages(user_message: str, session: dict, booking_dao: BookingDAO):
  reply_messages = []
  if user_message == line_config.USER_COMMAND_CANCEL_CLOSURE__CANCEL:
    # clear session data
    session['flow'], session['step'], session['data'] = None, None, {}
    reply_messages.append(TextSendMessage(text="好的，沒有取消"))

  elif user_message == line_config.USER_COMMAND_CANCEL_CLOSURE__CONFIRM:
    success = booking_dao.delete_closure(session['data']['closure_id'])
    reply_messages.append(TextSendMessage(text=("已取消關房" if success else "取消關房時遇到錯誤")))
    session['flow'], session['step'], session['data'] = None, None, {}

  else:
    quick_reply_buttons = [
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_CANCEL_CLOSURE__CANCEL,
        text=line_config.USER_COMMAND_CANCEL_CLOSURE__CANCEL)
      ),
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_CANCEL_CLOSURE__CONFIRM,
        text=line_config.USER_COMMAND_CANCEL_CLOSURE__CONFIRM)
      ),
    ]
    reply_messages.append(TextSendMessage(text=f"是否取消關房 #{session['data']['closure_id']}？", quick_reply=QuickReply(items=quick_reply_buttons)))
  return reply_messages
