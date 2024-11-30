import json
from datetime import datetime, timedelta
from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction, DatetimePickerAction
from const.booking_const import VALID_BOOKING_SOURCES
from app_const import line_config
from utils.data_access.booking_dao import BookingDAO
from utils.booking_utils import format_booking_changes
from utils.input_utils import is_valid_date, is_valid_phone_number, is_valid_num_nights, is_valid_price
from app_utils.line_messaging_utils import generate_edit_booking_select_attribute_quick_reply_buttons, generate_go_to_previous_step_button

def handle_edit_booking_messages(user_message: str, session: dict, booking_dao: BookingDAO):
  reply_messages = []
  quick_reply_buttons = [
    QuickReplyButton(action=MessageAction(
      label=line_config.USER_COMMAND_EDIT_BOOKING__FINISH,
      text=line_config.USER_COMMAND_EDIT_BOOKING__FINISH)
    )
  ]

  if user_message == line_config.USER_COMMAND_CANCEL_CURRENT_FLOW:
    # clear session data
    session['flow'], session['step'], session['data'] = None, None, {}
    reply_messages.append(TextSendMessage(text="已取消"))
    return reply_messages

  if user_message == line_config.USER_COMMAND_EDIT_BOOKING__FINISH:
    quick_reply_buttons = [
      QuickReplyButton(action=MessageAction(
        label='不要儲存',
        text=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW)
      ),
      QuickReplyButton(action=MessageAction(
        label='儲存變更',
        text=line_config.USER_COMMAND_CONFIRM)
      ),
    ]
    reply_messages.append(TextSendMessage(text=f"是否儲存變更？\n{format_booking_changes(session['data'])}", quick_reply=QuickReply(items=quick_reply_buttons)))
    session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__CONFIRM
    return reply_messages

  if user_message == line_config.USER_COMMAND_GO_TO_PREVIOUS_STEP_OF_CURRENT_FLOW:
    quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
    reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))
    session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE
    return reply_messages

  if session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE:
    quick_reply_buttons.append(generate_go_to_previous_step_button())
    if user_message == line_config.USER_COMMAND_EDIT_BOOKING__EDIT_CUSTOMER_NAME:
      reply_messages.append(TextSendMessage(text="請輸入顧客姓名:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_CUSTOMER_NAME
    elif user_message == line_config.USER_COMMAND_EDIT_BOOKING__EDIT_PHONE_NUMBER:
      reply_messages.append(TextSendMessage(text="請輸入顧客電話:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_PHONE_NUMBER
    elif user_message == line_config.USER_COMMAND_EDIT_BOOKING__EDIT_DATES:
      reply_messages.append(TextSendMessage(text="請輸入入住日期:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_CHECK_IN_DATE
    elif user_message == line_config.USER_COMMAND_EDIT_BOOKING__EDIT_ROOMS:
      session['data']['room_ids'] = []
      available_room_ids = booking_dao.get_all_room_ids()
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(label=room_id, text=room_id)) for room_id in available_room_ids
      ]
      reply_messages.append(TextSendMessage(text="請選擇入住房間:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_ROOMS
    elif user_message == line_config.USER_COMMAND_EDIT_BOOKING__EDIT_TOTAL_PRICE:
      reply_messages.append(TextSendMessage(text="請輸入總金額:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_TOTAL_PRICE
    elif user_message == line_config.USER_COMMAND_EDIT_BOOKING__EDIT_PREPAYMENT:
      reply_messages.append(TextSendMessage(text="請輸入訂金:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_PREPAYMENT
    elif user_message == line_config.USER_COMMAND_EDIT_BOOKING__EDIT_SOURCE:
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(label=source,text=source)) for source in VALID_BOOKING_SOURCES
      ]
      reply_messages.append(TextSendMessage(text="請選擇來源:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_SOURCE
    elif user_message == line_config.USER_COMMAND_EDIT_BOOKING__EDIT_NOTES:
      reply_messages.append(TextSendMessage(text="請輸入備註:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_NOTES
    else:
      quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
      reply_messages.append(TextSendMessage(text="輸入有誤，請重新選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))

  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_CUSTOMER_NAME:
    if not user_message:
      quick_reply_buttons = [generate_go_to_previous_step_button()]
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新輸入顧客姓名:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['customer_name'] = user_message
      quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
      reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE

  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_PHONE_NUMBER:
    if not is_valid_phone_number(user_message):
      quick_reply_buttons = [generate_go_to_previous_step_button()]
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新輸入顧客電話:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['phone_number'] = user_message
      quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
      reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE

  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_CHECK_IN_DATE:
    if not is_valid_date(user_message):
      quick_reply_buttons = [generate_go_to_previous_step_button()]
      quick_reply_buttons.append(
        QuickReplyButton(action=DatetimePickerAction(
          label="選擇入住日期",
          data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_EDIT_BOOKING__SELECT_CHECK_IN_DATE }),
          mode="date")
        )
      )
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新選擇入住日期:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['check_in_date'] = datetime.strptime(user_message, '%Y-%m-%d')
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_NUM_NIGHTS_1,
          text='1')
        ),
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_NUM_NIGHTS_2,
          text='2')
        ),
      ]
      reply_messages.append(TextSendMessage(text="請輸入入住晚數:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_NUM_NIGHTS

  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_NUM_NIGHTS:
    if not is_valid_num_nights(user_message):
      quick_reply_buttons = [generate_go_to_previous_step_button()]
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_NUM_NIGHTS_1,
          text='1')
        ),
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_NUM_NIGHTS_2,
          text='2')
        ),
      ]
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新輸入入住晚數(1~15):", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['num_nights'] = int(user_message)
      session['data']['last_date'] = session['data']['check_in_date'] + timedelta(days=session['data']['num_nights'] - 1)
      quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
      reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE

  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_ROOMS:
    if user_message != line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_ROOMS_FINISH:
      available_room_ids = booking_dao.get_all_room_ids()
      available_room_ids = [room_id for room_id in available_room_ids if room_id not in session['data']['room_ids']]
      if user_message not in available_room_ids:
        quick_reply_buttons += [
          QuickReplyButton(action=MessageAction(label=room_id, text=room_id)) for room_id in available_room_ids
        ]
        reply_messages.append(TextSendMessage(text=f"輸入格式有誤，請選擇入住房間:\n(已選[{''.join(session['data']['room_ids'])}])", quick_reply=QuickReply(items=quick_reply_buttons)))
      else:
        session['data']['room_ids'].append(user_message)
        quick_reply_buttons.append(
          QuickReplyButton(action=MessageAction(
            label=line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_ROOMS_FINISH,
            text=line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_ROOMS_FINISH)
          )
        )
        quick_reply_buttons += [
          QuickReplyButton(action=MessageAction(
            label=room_id,
            text=room_id)
          ) for room_id in available_room_ids if room_id != user_message
        ]
        reply_messages.append(TextSendMessage(text=f"請選擇入住房間:\n(已選[{''.join(session['data']['room_ids'])}])", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
      reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE

  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_TOTAL_PRICE:
    if not is_valid_price(user_message):
      quick_reply_buttons = [generate_go_to_previous_step_button()]
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新輸入總金額(0~100000):", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['total_price'] = int(user_message)
      quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
      reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE
  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_PREPAYMENT:
    if not is_valid_price(user_message):
      quick_reply_buttons = [generate_go_to_previous_step_button()]
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新輸入訂金(0~100000):", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['prepayment'] = int(user_message)
      quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
      reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE

  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_SOURCE:
    if user_message not in VALID_BOOKING_SOURCES:
      quick_reply_buttons = [generate_go_to_previous_step_button()]
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(label=source,text=source)) for source in VALID_BOOKING_SOURCES
      ]
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新輸入訂單來源:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['source'] = user_message
      quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
      reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE

  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__EDIT_NOTES:
    session['data']['notes'] = user_message
    quick_reply_buttons += generate_edit_booking_select_attribute_quick_reply_buttons()
    reply_messages.append(TextSendMessage(text="請選擇要更改的項目:", quick_reply=QuickReply(items=quick_reply_buttons)))
    session['step'] = line_config.USER_FLOW_STEP_EDIT_BOOKING__SELECT_ATTRIBUTE

  elif session['step'] == line_config.USER_FLOW_STEP_EDIT_BOOKING__CONFIRM:
    if user_message != line_config.USER_COMMAND_CONFIRM:
      quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(
          label='不要儲存',
          text=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW)
        ),
        QuickReplyButton(action=MessageAction(
          label='儲存變更',
          text=line_config.USER_COMMAND_CONFIRM)
        ),
      ]
      reply_messages.append(TextSendMessage(text=f"是否儲存變更？\n{format_booking_changes(session['data'])}", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      booking_info = booking_dao.get_booking_info(session['data']['booking_id'])
      if ('customer_name' in session['data']):
        booking_info.customer_name = session['data']['customer_name']
      if ('phone_number' in session['data']):
        booking_info.phone_number = session['data']['phone_number']
      if ('check_in_date' in session['data']):
        booking_info.check_in_date = session['data']['check_in_date']
      if ('last_date' in session['data']):
        booking_info.last_date = session['data']['last_date']
      if ('total_price' in session['data']):
        booking_info.total_price = session['data']['total_price']
      if ('notes' in session['data']):
        booking_info.notes = session['data']['notes']
      if ('source' in session['data']):
        booking_info.source = session['data']['source']
      if ('prepayment' in session['data']):
        booking_info.prepayment = session['data']['prepayment']
      if ('room_ids' in session['data']):
        booking_info.room_ids = ''.join(session['data']['room_ids'])
      if ('phone_number' in session['data']):
        booking_info.phone_number = session['data']['phone_number']
      booking_id = booking_dao.upsert_booking(booking_info)
      reply_messages.append(TextSendMessage(text=f"訂單ID{booking_id}已更改完成"))

      # clear session data
      session['flow'], session['step'], session['data'] = None, None, {}
  return reply_messages
