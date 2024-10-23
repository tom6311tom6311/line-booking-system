import re
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage,  QuickReply, QuickReplyButton, DatetimePickerAction
from const import db_config
from const.line_config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, USER_COMMAND_SEARCH_BOOKING_BY_KEYWORD, USER_COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE, POSTBACK_COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE, POSTBACK_COMMAND_VIEW_FULL_BOOKING_INFO
from data_access.booking_dao import BookingDAO
from utils.datetime_utils import is_valid_date, extract_date_from_string_template
from utils.booking_utils import format_booking_info
from utils.line_messaging_utils import create_booking_carousel_message

app = Flask(__name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
booking_dao = BookingDAO.get_instance(db_config, app.logger)

# RESTful handlers
@app.route('/bookings/<booking_id>')
def get_booking(booking_id):
  # app.logger.debug("A log message in level debug")
  # app.logger.info("A log message in level info")
  # app.logger.warning("A log message in level warning")
  # app.logger.error("A log message in level error")
  # app.logger.critical("A log message in level critical")
  booking_info = booking_dao.get_booking_info(int(booking_id))
  app.logger.info(booking_info.booking_id)
  reply_message = format_booking_info(booking_info, 'normal') or "找不到ID對應的訂單"
  return reply_message

@app.route('/query/bookings/<keyword>')
def search_bookings(keyword):
  matches = None
  if is_valid_date(keyword):
    matches = booking_dao.search_booking_by_check_in_date(keyword)
  else:
    matches = booking_dao.search_booking_by_keyword(keyword)
  if not matches:
    reply_message = "找不到任何訂單"
  else:
    reply_message = '\n\n'.join([format_booking_info(match, 'carousel') for match in matches])
  return reply_message

# LINE messaging API handlers
@app.route("/callback", methods=['POST'])
def callback():
  signature = request.headers['X-Line-Signature']
  body = request.get_data(as_text=True)
  try:
    handler.handle(body, signature)
  except InvalidSignatureError:
    abort(400)
  return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  user_message = event.message.text
  app.logger.debug(f"User message: {user_message}")

  reply_messages = []
  if user_message == USER_COMMAND_SEARCH_BOOKING_BY_KEYWORD:
    quick_reply_buttons = [
      QuickReplyButton(action=DatetimePickerAction(
        label="以入住日查詢",
        data=json.dumps({ 'command': POSTBACK_COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE }),
        mode="date")
      )
    ]

    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="請提供關鍵字:\n(ID、電話末3碼、姓名)", quick_reply=quick_reply))

  else:
    # Assuming the user provides a keyword
    keyword = user_message
    matches = booking_dao.search_booking_by_keyword(keyword)

    if not matches:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))
    else:
      reply_messages.append(create_booking_carousel_message(matches))

  if (len(reply_messages) > 0):
    line_bot_api.reply_message(
      event.reply_token,
      reply_messages
    )

@handler.add(PostbackEvent)
def handle_message_postback(event):
  command_obj = None
  try:
    command_obj = json.loads(event.postback.data)
  except ValueError:
    app.logger.error("Failed to parse postback event data as json")
    return

  reply_messages = []
  if command_obj['command'] == POSTBACK_COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE:
    selected_date = event.postback.params['date']

    reply_messages.append(TextSendMessage(USER_COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE.format(date=selected_date.replace('-', '/'))))

    matches = booking_dao.search_booking_by_check_in_date(selected_date)
    if not matches:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))
    else:
      reply_messages.append(create_booking_carousel_message(matches))

  elif command_obj['command'] == POSTBACK_COMMAND_VIEW_FULL_BOOKING_INFO:
    booking_id = command_obj['booking_id']
    booking_info = booking_dao.get_booking_info(int(booking_id))

    reply_messages.append(TextSendMessage(format_booking_info(booking_info, 'normal') or "找不到ID對應的訂單"))

  else:
    app.logger.warning(f"Unrecognized postback command: {command_obj['command']}")

  if (len(reply_messages) > 0):
    line_bot_api.reply_message(
        event.reply_token,
        reply_messages
      )
if __name__ == "__main__":
  app.run(debug=True)
