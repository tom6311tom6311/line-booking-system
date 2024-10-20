from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage,  QuickReply, QuickReplyButton, DatetimePickerAction
from const import db_config
from const.line_config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, COMMAND_BOOKING_LOOKUP, COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE
from data_access.booking_dao import BookingDAO
from utils.datetime_utils import is_valid_date
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
  reply_message = format_booking_info(booking_info) or "找不到ID對應的訂單"
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

  if user_message == COMMAND_BOOKING_LOOKUP:
    quick_reply_buttons = [
      QuickReplyButton(action=DatetimePickerAction(label="以入住日查詢", data=COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE, mode="date"))
    ]

    quick_reply = QuickReply(items=quick_reply_buttons)
    line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="請提供關鍵字:\n(ID、電話末3碼、姓名)", quick_reply=quick_reply)
    )
  else:
    # Assuming the user provides a keyword
    keyword = user_message
    matches = booking_dao.search_booking_by_keyword(keyword)

    if not matches:
      reply_message = TextSendMessage(text="找不到任何訂單")
    else:
      reply_message = create_booking_carousel_message(matches)

    # Send the reply (either results or no matches)
    line_bot_api.reply_message(
      event.reply_token,
      reply_message
    )

@handler.add(PostbackEvent)
def handle_message_postback(event):
  if event.postback.data == COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE:
    selected_date = event.postback.params['date']

    line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text=f"查詢{selected_date.replace('-', '/')}入住的訂單...")
    )

    matches = booking_dao.search_booking_by_check_in_date(selected_date)
    if not matches:
      reply_message = TextSendMessage(text="找不到任何訂單")
    else:
      reply_message = create_booking_carousel_message(matches)

    line_bot_api.reply_message(
      event.reply_token,
      reply_message
    )

if __name__ == "__main__":
  app.run(debug=True)
