import os
import datetime
import psycopg2
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

BOOKING_STATUS_MARK = {
  'canceled': '[取消]'
}

PREPAYMENT_STATUS_MAP = {
  'unpaid': '未付',
  'paid': '已付'
}

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
# base_url = os.getenv('BASE_URL')

# DB Connection details
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Function to query the booking info by booking_id
def get_booking_info(booking_id):
  conn = None
  booking_info = None
  try:
    conn = psycopg2.connect(
      host=DB_HOST,
      dbname=DB_NAME,
      user=DB_USER,
      password=DB_PASSWORD
    )
    cursor = conn.cursor()

    # Query to retrieve the booking and related customer and room information
    query = """
    SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date, 
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_status,
        STRING_AGG(r.room_id, '') AS room_ids
    FROM Bookings b
    JOIN Customers c ON b.customer_id = c.customer_id
    JOIN RoomBookings rb ON b.booking_id = rb.booking_id
    JOIN Rooms r ON rb.room_id = r.room_id
    WHERE b.booking_id = %s
    GROUP BY b.booking_id, c.name, c.phone_number;
    """

    cursor.execute(query, (booking_id,))
    booking_info = cursor.fetchone()
    cursor.close()

  except Exception as e:
    print(f"Error: {e}")

  finally:
    if conn:
      conn.close()

  return booking_info

# Function to format the booking info as per the required format
def format_booking_info(booking_info):
  if not booking_info:
    return None

  booking_id, status, customer_name, phone_number, check_in, last_date, total_price, notes, source, prepayment, prepayment_status, room_ids = booking_info

  if phone_number.startswith('+886'):
    phone_number = '0' + phone_number[4:]
  total_price = int(total_price)
  prepayment = int(prepayment)

  status_mark = BOOKING_STATUS_MARK[status] if status in BOOKING_STATUS_MARK else ''

  # Calculate the number of nights
  nights = (last_date - check_in).days + 1
  check_out = last_date + datetime.timedelta(days=1)

  prepayment_status = PREPAYMENT_STATUS_MAP[prepayment_status]

  # Format the response message
  message = (
    f"[訂單]{status_mark}\n"
    f"ＩＤ：{booking_id}\n"
    f"姓名：{customer_name}\n"
    f"電話：{phone_number}\n"
    f"入住日期：{check_in.strftime('%Y/%m/%d')}\n"
    f"退房日期：{check_out.strftime('%Y/%m/%d')}\n"
    f"晚數：{nights}\n"
    f"總金額：{total_price}\n"
    f"備註：{notes}\n"
    f"來源：{source}\n"
    f"訂金：{prepayment}元/{prepayment_status}\n"
    f"預計讓他睡：{room_ids}\n"
  )

  return message

@app.route('/bookings/<booking_id>')
def get_booking(booking_id):
  # app.logger.debug("A log message in level debug")
  # app.logger.info("A log message in level info")
  # app.logger.warning("A log message in level warning")
  # app.logger.error("A log message in level error")
  # app.logger.critical("A log message in level critical")
  booking_info = get_booking_info(int(booking_id))
  reply_message = format_booking_info(booking_info) or "找不到ID對應的訂單"
  return reply_message

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
    booking_info = get_booking_info(booking_id)
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
