from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from const import db_config
from const.line_config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from data_access.booking_dao import BookingDAO
from utils.booking_utils import format_booking_info

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
  # Try to get booking_id from user message (assuming it's a valid integer)
  try:
    booking_id = int(event.message.text)
    booking_info = booking_dao.get_booking_info(booking_id)
    reply_message = format_booking_info(booking_info) or "找不到ID對應的訂單"
  except ValueError:
    reply_message = "ID 應該是個數字哦"

  # Send the response back to the user
  line_bot_api.reply_message(
    event.reply_token,
    TextSendMessage(text=reply_message)
  )

if __name__ == "__main__":
  app.run(debug=True)
