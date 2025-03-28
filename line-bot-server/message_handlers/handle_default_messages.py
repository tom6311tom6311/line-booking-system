import json
import datetime
from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction, DatetimePickerAction
from const import line_config
from utils.input_utils import extract_booking_id
from utils.data_access.booking_dao import BookingDAO
from utils.line_messaging_utils import generate_booking_carousel_message, generate_closure_carousel_message, generate_edit_booking_select_attribute_quick_reply_buttons

def handle_default_messages(user_message: str, session: dict, booking_dao: BookingDAO):
  reply_messages = []
  if user_message == line_config.USER_COMMAND_SEARCH_BOOKING_BY_KEYWORD:
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
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_SEARCH_BOOKING_NOT_PREPAID,
        text=line_config.USER_COMMAND_SEARCH_BOOKING_NOT_PREPAID)
      ),
    ]
    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="請提供關鍵字:\n(ID、電話末3碼、姓名)", quick_reply=quick_reply))

  elif user_message == line_config.USER_COMMAND_SEARCH_BOOKING_CHECK_OUT_TODAY:
    date_yesterday = datetime.date.today() + datetime.timedelta(days=-1)
    matched_bookings = booking_dao.search_booking_by_date(date_yesterday.strftime('%Y-%m-%d'), mode='last_date')
    if not matched_bookings:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))
    else:
      reply_messages.append(generate_booking_carousel_message(matched_bookings, show_edit_actions=True))

  elif user_message == line_config.USER_COMMAND_SEARCH_BOOKING_TODAY:
    date_today = datetime.date.today()
    matched_bookings = booking_dao.search_booking_by_date(date_today.strftime('%Y-%m-%d'))
    if matched_bookings:
      reply_messages.append(generate_booking_carousel_message(matched_bookings, show_edit_actions=True))

    matched_closures = booking_dao.search_closure_by_date(date_today.strftime('%Y-%m-%d'))
    if matched_closures:
      reply_messages.append(generate_closure_carousel_message(matched_closures, show_edit_actions=True))

    if not matched_bookings and not matched_closures:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))

  elif user_message == line_config.USER_COMMAND_SEARCH_BOOKING_TOMORROW:
    date_tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    matched_bookings = booking_dao.search_booking_by_date(date_tomorrow.strftime('%Y-%m-%d'))
    if matched_bookings:
      reply_messages.append(generate_booking_carousel_message(matched_bookings, show_edit_actions=True))

    matched_closures = booking_dao.search_closure_by_date(date_tomorrow.strftime('%Y-%m-%d'))
    if matched_closures:
      reply_messages.append(generate_closure_carousel_message(matched_closures, show_edit_actions=True))

    if not matched_bookings and not matched_closures:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))

  elif user_message == line_config.USER_COMMAND_SEARCH_BOOKING_THIS_SATURDAY:
    date_today = datetime.date.today()
    delta_days_to_this_saturday = 5 - date_today.weekday()
    date_this_saturday = date_today + datetime.timedelta(days=delta_days_to_this_saturday)
    matched_bookings = booking_dao.search_booking_by_date(date_this_saturday.strftime('%Y-%m-%d'))
    if matched_bookings:
      reply_messages.append(generate_booking_carousel_message(matched_bookings, show_edit_actions=True))

    matched_closures = booking_dao.search_closure_by_date(date_this_saturday.strftime('%Y-%m-%d'))
    if matched_closures:
      reply_messages.append(generate_closure_carousel_message(matched_closures, show_edit_actions=True))

    if not matched_bookings and not matched_closures:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))

  elif user_message == line_config.USER_COMMAND_SEARCH_BOOKING_LAST_SATURDAY:
    date_today = datetime.date.today()
    delta_days_to_last_saturday = -2 - date_today.weekday()
    date_last_saturday = date_today + datetime.timedelta(days=delta_days_to_last_saturday)
    matched_bookings = booking_dao.search_booking_by_date(date_last_saturday.strftime('%Y-%m-%d'))
    if matched_bookings:
      reply_messages.append(generate_booking_carousel_message(matched_bookings, show_edit_actions=True))

    matched_closures = booking_dao.search_closure_by_date(date_last_saturday.strftime('%Y-%m-%d'))
    if matched_closures:
      reply_messages.append(generate_closure_carousel_message(matched_closures, show_edit_actions=True))

    if not matched_bookings and not matched_closures:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))

  elif user_message == line_config.USER_COMMAND_SEARCH_BOOKING_NOT_PREPAID:
    matched_bookings = booking_dao.search_booking_not_prepaid()
    if not matched_bookings:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))
    else:
      reply_messages.append(generate_booking_carousel_message(matched_bookings, show_edit_actions=True))

  elif user_message == line_config.USER_COMMAND_CREATE_BOOKING:
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

  elif booking_id := extract_booking_id(user_message, line_config.USER_COMMAND_EDIT_BOOKING):
    quick_reply_buttons = [
      QuickReplyButton(action=MessageAction(
        label=line_config.USER_COMMAND_EDIT_BOOKING__FINISH,
        text=line_config.USER_COMMAND_EDIT_BOOKING__FINISH)
      ),
    ]
    quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
    quick_reply = QuickReply(items=quick_reply_buttons)
    reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=quick_reply))
    session['flow'] = line_config.USER_FLOW_EDIT_BOOKING
    session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE
    session['data'] = { 'booking_id': booking_id }

  else:
    # Assuming the user provides a keyword
    keyword = user_message
    matches = booking_dao.search_booking_by_keyword(keyword)

    if not matches:
      reply_messages.append(TextSendMessage(text="找不到任何訂單"))
    else:
      reply_messages.append(generate_booking_carousel_message(matches, show_edit_actions=True))

  return reply_messages
