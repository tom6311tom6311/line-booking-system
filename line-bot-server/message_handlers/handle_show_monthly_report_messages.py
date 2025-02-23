from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction
from const import line_config
from utils.data_access.booking_dao import BookingDAO
from utils.input_utils import is_valid_date
from utils.datetime_utils import get_latest_months
from utils.booking_utils import generate_report

def handle_show_monthly_report_messages(user_message: str, session: dict, booking_dao: BookingDAO):
  reply_messages = []
  quick_reply_buttons = []

  if user_message == line_config.USER_COMMAND_CANCEL_CURRENT_FLOW:
    # clear session data
    session['flow'], session['step'], session['data'] = None, None, {}
    reply_messages.append(TextSendMessage(text="已取消"))
    return reply_messages

  if session['step'] == line_config.USER_FLOW_STEP_SHOW_MONTHLY_REPORT__SELECT_MONTH:
    if not is_valid_date(user_message, '%Y-%m'):
      quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW,
          text=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW)
        ),
        *[
          QuickReplyButton(action=MessageAction(
            label=year_month,
            text=year_month)
          )
          for year_month in get_latest_months(3, '%Y-%m')
        ]
      ]
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新選擇月份:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['year_month'] = user_message
      bookings = booking_dao.get_bookings_by_month(session['data']['year_month'])
      report_text = generate_report(session['data']['year_month'], bookings)
      reply_messages.append(TextSendMessage(text=report_text))

      # clear session data
      session['flow'], session['step'], session['data'] = None, None, {}

  return reply_messages
