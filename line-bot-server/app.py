import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage
from const import db_config
from app_const import line_config
from utils.data_access.booking_dao import BookingDAO
from utils.booking_utils import format_booking_info
from utils.input_utils import is_valid_date
from app_utils.line_messaging_utils import create_booking_carousel_message
from message_handlers.handle_default_messages import handle_default_messages
from message_handlers.handle_create_booking_messages import handle_create_booking_messages

app = Flask(__name__)

line_bot_api = LineBotApi(line_config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(line_config.LINE_CHANNEL_SECRET)
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
    matches = booking_dao.search_booking_by_date(keyword)
  else:
    matches = booking_dao.search_booking_by_keyword(keyword)
  if not matches:
    reply_message = "找不到任何訂單"
  else:
    reply_message = '\n\n'.join([format_booking_info(match, 'carousel') for match in matches])
  return reply_message

# In-memory session store for LINE messaging API
user_sessions = {}

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
  user_id = event.source.user_id
  user_message = event.message.text
  app.logger.debug(f"User Id: {user_id}, message: {user_message}")

  # Initialize session if user is new
  if user_id not in user_sessions:
    user_sessions[user_id] = { 'flow': None, 'step': None, 'data': {} }

  session = user_sessions[user_id]
  reply_messages = []
  if not session['flow']:
    reply_messages = handle_default_messages(user_message, session, booking_dao)

  elif user_message == line_config.USER_COMMAND_CANCEL_CURRENT_FLOW:
    del user_sessions[user_id]
    reply_messages.append(TextSendMessage(text="已取消"))

  elif session['flow'] == line_config.USER_FLOW_CREATE_BOOKING:
    reply_messages = handle_create_booking_messages(user_message, session)

  if (len(reply_messages) > 0):
    line_bot_api.reply_message(
      event.reply_token,
      reply_messages
    )

@handler.add(PostbackEvent)
def handle_message_postback(event):
  user_id = event.source.user_id
  command_obj = None
  try:
    command_obj = json.loads(event.postback.data)
  except ValueError:
    app.logger.error("Failed to parse postback event data as json")
    return
  app.logger.debug(f"User Id: {user_id}, postback event: {command_obj}")

  # Initialize session if user is new
  if user_id not in user_sessions:
    user_sessions[user_id] = { 'flow': None, 'step': None, 'data': {} }

  session = user_sessions[user_id]
  reply_messages = []
  if command_obj['command'] == line_config.POSTBACK_COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE:
    selected_date = event.postback.params['date']
    reply_messages.append(TextSendMessage(line_config.USER_COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE.format(date=selected_date.replace('-', '/'))))

    matches = booking_dao.search_booking_by_date(selected_date)
    if not matches:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))
    else:
      reply_messages.append(create_booking_carousel_message(matches))

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_VIEW_FULL_BOOKING_INFO:
    booking_id = command_obj['booking_id']
    booking_info = booking_dao.get_booking_info(int(booking_id))

    reply_messages.append(TextSendMessage(format_booking_info(booking_info, 'normal') or "找不到ID對應的訂單"))

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_CREATE_BOOKING__SELECT_CHECK_IN_DATE:
    selected_date = event.postback.params['date']
    reply_messages = handle_create_booking_messages(selected_date, session)

  else:
    app.logger.warning(f"Unrecognized postback command: {command_obj['command']}")

  if (len(reply_messages) > 0):
    line_bot_api.reply_message(
        event.reply_token,
        reply_messages
      )
if __name__ == "__main__":
  app.run(debug=True)
