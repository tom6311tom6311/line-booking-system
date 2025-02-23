import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction, DatetimePickerAction
from const import db_config
from app_const import line_config
from utils.data_access.booking_dao import BookingDAO
from utils.booking_utils import format_booking_info
from utils.closure_utils import format_closure_info
from utils.input_utils import is_valid_date
from utils.datetime_utils import get_latest_months
from app_utils.line_messaging_utils import generate_booking_carousel_message, generate_closure_carousel_message
from message_handlers.handle_default_messages import handle_default_messages
from message_handlers.handle_create_booking_messages import handle_create_booking_messages
from message_handlers.handle_edit_booking_messages import handle_edit_booking_messages
from message_handlers.handle_cancel_booking_messages import handle_cancel_booking_messages
from message_handlers.handle_restore_booking_messages import handle_restore_booking_messages
from message_handlers.handle_prepaid_booking_messages import handle_prepaid_booking_messages
from message_handlers.handle_create_closure_messages import handle_create_closure_messages
from message_handlers.handle_cancel_closure_messages import handle_cancel_closure_messages
from message_handlers.handle_show_monthly_report_messages import handle_show_monthly_report_messages

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

@app.route('/query/closures/<date>')
def search_closures(date):
  matches = None
  if is_valid_date(date):
    matches = booking_dao.search_closure_by_date(date)

  if not matches:
    reply_message = "找不到任何關房資料"
  else:
    reply_message = '\n\n'.join([format_closure_info(match) for match in matches])
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

  elif session['flow'] == line_config.USER_FLOW_CREATE_BOOKING:
    reply_messages = handle_create_booking_messages(user_message, session, booking_dao)

  elif session['flow'] == line_config.USER_FLOW_EDIT_BOOKING:
    reply_messages = handle_edit_booking_messages(user_message, session, booking_dao)

  elif session['flow'] == line_config.USER_FLOW_CANCEL_BOOKING:
    reply_messages = handle_cancel_booking_messages(user_message, session, booking_dao)

  elif session['flow'] == line_config.USER_FLOW_RESTORE_BOOKING:
    reply_messages = handle_restore_booking_messages(user_message, session, booking_dao)

  elif session['flow'] == line_config.USER_FLOW_PREPAID_BOOKING:
    reply_messages = handle_prepaid_booking_messages(user_message, session, booking_dao)

  elif session['flow'] == line_config.USER_FLOW_CREATE_CLOSURE:
    reply_messages = handle_create_closure_messages(user_message, session, booking_dao)

  elif session['flow'] == line_config.USER_FLOW_CANCEL_CLOSURE:
    reply_messages = handle_cancel_closure_messages(user_message, session, booking_dao)

  elif session['flow'] == line_config.USER_FLOW_SHOW_MONTHLY_REPORT:
    reply_messages = handle_show_monthly_report_messages(user_message, session, booking_dao)

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
  if command_obj['command'] == line_config.POSTBACK_COMMAND_LOOKUP_BOOKING:
    quick_reply_buttons = [
      QuickReplyButton(action=DatetimePickerAction(
        label="以日期查詢",
        data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_SEARCH_BOOKING_BY_DATE }),
        mode="date")
      ),
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_SEARCH_BOOKING_TODAY,
        text=line_config.USER_COMMAND_SEARCH_BOOKING_TODAY)
      ),
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_SEARCH_BOOKING_CHECK_OUT_TODAY,
        text=line_config.USER_COMMAND_SEARCH_BOOKING_CHECK_OUT_TODAY)
      ),
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_SEARCH_BOOKING_TOMORROW,
        text=line_config.USER_COMMAND_SEARCH_BOOKING_TOMORROW)
      ),
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_SEARCH_BOOKING_THIS_SATURDAY,
        text=line_config.USER_COMMAND_SEARCH_BOOKING_THIS_SATURDAY)
      ),
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_SEARCH_BOOKING_LAST_SATURDAY,
        text=line_config.USER_COMMAND_SEARCH_BOOKING_LAST_SATURDAY)
      ),
    ]
    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="請提供關鍵字:\n(ID、電話末3碼、姓名)", quick_reply=quick_reply))

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_CREATE_BOOKING:
    quick_reply_buttons = [
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW,
        text=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW)
      ),
    ]
    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="請輸入顧客姓名:", quick_reply=quick_reply))
    session['flow'] = line_config.USER_FLOW_CREATE_BOOKING
    session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CUSTOMER_NAME
    session['data'] = {}

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_SEARCH_BOOKING_BY_DATE:
    selected_date = event.postback.params['date']
    reply_messages.append(TextSendMessage(line_config.USER_COMMAND_SEARCH_BOOKING_BY_DATE.format(date=selected_date.replace('-', '/'))))

    matched_bookings = booking_dao.search_booking_by_date(selected_date)
    if matched_bookings:
      reply_messages.append(generate_booking_carousel_message(matched_bookings))

    matched_closures = booking_dao.search_closure_by_date(selected_date)
    if matched_closures:
      reply_messages.append(generate_closure_carousel_message(matched_closures))

    if not matched_bookings and not matched_closures:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_VIEW_FULL_BOOKING_INFO:
    booking_id = command_obj['booking_id']
    booking_info = booking_dao.get_booking_info(int(booking_id))
    reply_messages.append(TextSendMessage(format_booking_info(booking_info, 'normal') or "找不到ID對應的訂單"))

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_CANCEL_BOOKING:
    booking_id = command_obj['booking_id']
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
    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="是否真的要取消此訂單？", quick_reply=quick_reply))
    session['flow'] = line_config.USER_FLOW_CANCEL_BOOKING
    session['step'] = line_config.USER_FLOW_STEP_CANCEL_BOOKING__CONFIRM
    session['data'] = { 'booking_id': booking_id }

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_RESTORE_BOOKING:
    booking_id = command_obj['booking_id']
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
    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="是否真的要復原此訂單？", quick_reply=quick_reply))
    session['flow'] = line_config.USER_FLOW_RESTORE_BOOKING
    session['step'] = line_config.USER_FLOW_STEP_RESTORE_BOOKING__CONFIRM
    session['data'] = { 'booking_id': booking_id }

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_PREPAID_BOOKING:
    booking_id = command_obj['booking_id']
    booking_info = booking_dao.get_booking_info(int(booking_id))
    prepayment = str(int(booking_info.prepayment))
    quick_reply_buttons = [
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW,
        text=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW)
      ),
      QuickReplyButton(action=MessageAction(
        label=prepayment,
        text=prepayment)
      )
    ]
    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="請輸入已付訂金金額：", quick_reply=quick_reply))
    session['flow'] = line_config.USER_FLOW_PREPAID_BOOKING
    session['step'] = line_config.USER_FLOW_STEP_PREPAID_BOOKING__GET_PREPAYMENT_AMOUNT
    session['data'] = { 'booking_id': booking_id }

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_CREATE_CLOSURE:
    quick_reply_buttons = [
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW,
        text=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW)
      ),
      QuickReplyButton(action=DatetimePickerAction(
        label="選擇日期",
        data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_CREATE_CLOSURE__SELECT_START_DATE }),
        mode="date")
      ),
    ]
    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="請輸入關房日期:", quick_reply=quick_reply))
    session['flow'] = line_config.USER_FLOW_CREATE_CLOSURE
    session['step'] = line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_START_DATE
    session['data'] = {}

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_CANCEL_CLOSURE:
    closure_id = command_obj['closure_id']
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
    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="是否真的要取消關房？", quick_reply=quick_reply))
    session['flow'] = line_config.USER_FLOW_CANCEL_CLOSURE
    session['step'] = line_config.USER_FLOW_STEP_CANCEL_CLOSURE__CONFIRM
    session['data'] = { 'closure_id': closure_id }

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_CREATE_BOOKING__SELECT_CHECK_IN_DATE:
    selected_date = event.postback.params['date']
    reply_messages.append(TextSendMessage(line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_CHECK_IN_DATE.format(date=selected_date.replace('-', '/'))))
    reply_messages += handle_create_booking_messages(selected_date, session, booking_dao)

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_EDIT_BOOKING__SELECT_CHECK_IN_DATE:
    selected_date = event.postback.params['date']
    reply_messages.append(TextSendMessage(line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_CHECK_IN_DATE.format(date=selected_date.replace('-', '/'))))
    reply_messages += handle_edit_booking_messages(selected_date, session, booking_dao)

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_CREATE_CLOSURE__SELECT_START_DATE:
    selected_date = event.postback.params['date']
    reply_messages.append(TextSendMessage(line_config.USER_COMMAND_CREATE_CLOSURE__SELECT_START_DATE.format(date=selected_date.replace('-', '/'))))
    reply_messages += handle_create_closure_messages(selected_date, session, booking_dao)

  elif command_obj['command'] == line_config.POSTBACK_COMMAND_SHOW_MONTHLY_REPORT:
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

    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="請選擇月份:", quick_reply=quick_reply))
    session['flow'] = line_config.USER_FLOW_SHOW_MONTHLY_REPORT
    session['step'] = line_config.USER_FLOW_STEP_SHOW_MONTHLY_REPORT__SELECT_MONTH
    session['data'] = {}

  else:
    app.logger.warning(f"Unrecognized postback command: {command_obj['command']}")

  if (len(reply_messages) > 0):
    line_bot_api.reply_message(
        event.reply_token,
        reply_messages
      )
if __name__ == "__main__":
  app.run(debug=True)
