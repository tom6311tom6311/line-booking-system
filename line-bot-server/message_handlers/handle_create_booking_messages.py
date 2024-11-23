import json
from datetime import datetime, timedelta
from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction, DatetimePickerAction
from const.booking_const import VALID_BOOKING_SOURCES
from app_const import line_config
from utils.data_access.data_class.booking_info import BookingInfo
from utils.data_access.booking_dao import BookingDAO
from utils.booking_utils import format_booking_info
from utils.input_utils import is_valid_date, is_valid_phone_number, is_valid_num_nights, is_valid_price

PREVIOUS_STEP = {
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PHONE_NUMBER: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CUSTOMER_NAME,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CHECK_IN_DATE: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PHONE_NUMBER,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NUM_NIGHTS: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CHECK_IN_DATE,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_ROOMS: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CHECK_IN_DATE,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_TOTAL_PRICE: line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_ROOMS,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PREPAYMENT: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_TOTAL_PRICE,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_SOURCE: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PREPAYMENT,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NOTES: line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_SOURCE,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__CONFIRM: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NOTES,
}

def handle_create_booking_messages(user_message: str, session: dict, booking_dao: BookingDAO):
  reply_messages = []
  quick_reply_buttons = [
    QuickReplyButton(action=MessageAction(
      label=line_config.USER_COMMAND_GO_TO_PREVIOUS_STEP_OF_CURRENT_FLOW,
      text=line_config.USER_COMMAND_GO_TO_PREVIOUS_STEP_OF_CURRENT_FLOW)
    )
  ]

  if user_message == line_config.USER_COMMAND_CANCEL_CURRENT_FLOW:
    # clear session data
    session['flow'], session['step'], session['data'] = None, None, {}
    reply_messages.append(TextSendMessage(text="已取消"))
    return reply_messages

  is_previous_step = False
  if user_message == line_config.USER_COMMAND_GO_TO_PREVIOUS_STEP_OF_CURRENT_FLOW:
    if (session['step'] and PREVIOUS_STEP[session['step']]):
      session['step'] = PREVIOUS_STEP[session['step']]
      is_previous_step = True
      if session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_ROOMS:
        session['data']['room_ids'] = []
    else:
      session['flow'], session['step'], session['data'] = None, None, {}
      reply_messages.append(TextSendMessage(text="已取消"))
      return reply_messages

  if session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CUSTOMER_NAME:
    if is_previous_step or not user_message:
      quick_reply_buttons = [
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW,
          text=line_config.USER_COMMAND_CANCEL_CURRENT_FLOW)
        )
      ]
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新輸入顧客姓名:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['customer_name'] = user_message
      reply_messages.append(TextSendMessage(text="請輸入顧客電話:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PHONE_NUMBER

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PHONE_NUMBER:
    if is_previous_step or not is_valid_phone_number(user_message):
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新輸入顧客電話:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['phone_number'] = user_message
      quick_reply_buttons.append(
        QuickReplyButton(action=DatetimePickerAction(
          label="選擇入住日期",
          data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_CREATE_BOOKING__SELECT_CHECK_IN_DATE }),
          mode="date")
        )
      )
      reply_messages.append(TextSendMessage(text="請選擇入住日期:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CHECK_IN_DATE

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CHECK_IN_DATE:
    if is_previous_step or not is_valid_date(user_message):
      quick_reply_buttons.append(
        QuickReplyButton(action=DatetimePickerAction(
          label="選擇入住日期",
          data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_CREATE_BOOKING__SELECT_CHECK_IN_DATE }),
          mode="date")
        )
      )
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新選擇入住日期:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['check_in_date'] = datetime.strptime(user_message, '%Y-%m-%d')
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_BOOKING__SELECT_NUM_NIGHTS_1,
          text='1')
        ),
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_BOOKING__SELECT_NUM_NIGHTS_2,
          text='2')
        ),
      ]
      reply_messages.append(TextSendMessage(text="請輸入入住晚數:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NUM_NIGHTS

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NUM_NIGHTS:
    if not is_valid_num_nights(user_message):
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_BOOKING__SELECT_NUM_NIGHTS_1,
          text='1')
        ),
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_BOOKING__SELECT_NUM_NIGHTS_2,
          text='2')
        ),
      ]
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新輸入入住晚數(1~15):", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['num_nights'] = int(user_message)
      session['data']['last_date'] = session['data']['check_in_date'] + timedelta(days=session['data']['num_nights'] - 1)
      session['data']['room_ids'] = []
      available_room_ids = booking_dao.get_available_room_ids(session['data']['check_in_date'], session['data']['last_date'])
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=room_id,
          text=room_id)
        ) for room_id in available_room_ids
      ]
      reply_messages.append(TextSendMessage(text="請選擇入住房間:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_ROOMS

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_ROOMS:
    if user_message != line_config.USER_COMMAND_CREATE_BOOKING__SELECT_ROOMS_FINISH:
      valid_room_ids = booking_dao.get_all_room_ids()
      available_room_ids = booking_dao.get_available_room_ids(session['data']['check_in_date'], session['data']['last_date'])
      available_room_ids = [room_id for room_id in available_room_ids if room_id not in session['data']['room_ids']]
      if is_previous_step or user_message not in valid_room_ids or user_message in session['data']['room_ids']:
        quick_reply_buttons += [
          QuickReplyButton(action=MessageAction(
            label=room_id,
            text=room_id)
          ) for room_id in available_room_ids
        ]
        reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請選擇入住房間:\n(已選[{''.join(session['data']['room_ids'])}])", quick_reply=QuickReply(items=quick_reply_buttons)))
      else:
        session['data']['room_ids'].append(user_message)
        quick_reply_buttons.append(
          QuickReplyButton(action=MessageAction(
            label=line_config.USER_COMMAND_CREATE_BOOKING__SELECT_ROOMS_FINISH,
            text=line_config.USER_COMMAND_CREATE_BOOKING__SELECT_ROOMS_FINISH)
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
      estimated_total_price = booking_dao.get_total_price_estimation(
        session['data']['room_ids'],
        session['data']['check_in_date'],
        session['data']['last_date']
      )
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=str(estimated_total_price),
          text=str(estimated_total_price))
        )
      )
      reply_messages.append(TextSendMessage(text="請輸入總金額:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_TOTAL_PRICE

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_TOTAL_PRICE:
    if is_previous_step or not is_valid_price(user_message):
      estimated_total_price = booking_dao.get_total_price_estimation(
        session['data']['room_ids'],
        session['data']['check_in_date'],
        session['data']['last_date']
      )
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=str(estimated_total_price),
          text=str(estimated_total_price))
        )
      )
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新輸入總金額(0~100000):", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['total_price'] = int(user_message)
      estimated_prepayment = int(session['data']['total_price'] * 0.3 // 100 * 100)
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=str(estimated_prepayment),
          text=str(estimated_prepayment))
        )
      )
      reply_messages.append(TextSendMessage(text="請輸入訂金:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PREPAYMENT

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PREPAYMENT:
    if is_previous_step or not is_valid_price(user_message):
      estimated_prepayment = int(session['data']['total_price'] * 0.3 // 100 * 100)
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=str(estimated_prepayment),
          text=str(estimated_prepayment))
        )
      )
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新輸入訂金(0~100000):", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['prepayment'] = int(user_message)
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=source,
          text=source)
        ) for source in VALID_BOOKING_SOURCES
      ]
      reply_messages.append(TextSendMessage(text="請輸入訂單來源:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_SOURCE

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_SOURCE:
    if is_previous_step or user_message not in VALID_BOOKING_SOURCES:
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=source,
          text=source)
        ) for source in VALID_BOOKING_SOURCES
      ]
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新輸入訂單來源:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['source'] = user_message
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_BOOKING__GET_NOTES_FINISH,
          text=line_config.USER_COMMAND_CREATE_BOOKING__GET_NOTES_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text="請輸入備註:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NOTES

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NOTES:
    if is_previous_step:
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_BOOKING__GET_NOTES_FINISH,
          text=line_config.USER_COMMAND_CREATE_BOOKING__GET_NOTES_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text="請輸入備註:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['notes'] = '' if user_message == line_config.USER_COMMAND_CREATE_BOOKING__GET_NOTES_FINISH else user_message
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_BOOKING__CONFIRM_FINISH,
          text=line_config.USER_COMMAND_CREATE_BOOKING__CONFIRM_FINISH)
        )
      )
      booking_info = BookingInfo(
        booking_id=-1,
        status='new',
        customer_name=session['data']['customer_name'],
        phone_number=session['data']['phone_number'],
        check_in_date=session['data']['check_in_date'],
        last_date=session['data']['last_date'],
        total_price=session['data']['total_price'],
        notes=session['data']['notes'],
        source=session['data']['source'],
        prepayment=session['data']['prepayment'],
        prepayment_note='',
        prepayment_status='unpaid',
        room_ids=''.join(session['data']['room_ids'])
      )
      booking_info_preview_text = format_booking_info(booking_info, 'normal')
      reply_messages.append(TextSendMessage(text=f"請確認訂單資訊:\n{booking_info_preview_text}", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__CONFIRM

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__CONFIRM:
    if user_message != line_config.USER_COMMAND_CREATE_BOOKING__CONFIRM_FINISH:
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_BOOKING__CONFIRM_FINISH,
          text=line_config.USER_COMMAND_CREATE_BOOKING__CONFIRM_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text=f"是否確認新增訂單？請點擊確認或取消", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      booking_info = BookingInfo(
        booking_id=-1,
        status='new',
        customer_name=session['data']['customer_name'],
        phone_number=session['data']['phone_number'],
        check_in_date=session['data']['check_in_date'],
        last_date=session['data']['last_date'],
        total_price=session['data']['total_price'],
        notes=session['data']['notes'],
        source=session['data']['source'],
        prepayment=session['data']['prepayment'],
        prepayment_note='',
        prepayment_status='unpaid',
        room_ids=''.join(session['data']['room_ids'])
      )
      booking_id = booking_dao.upsert_booking(booking_info)
      quick_reply_buttons = []
      reply_messages.append(TextSendMessage(text=f"訂單已新增完成, ID:{booking_id}", quick_reply=QuickReply(items=quick_reply_buttons)))

      # clear session data
      session['flow'], session['step'], session['data'] = None, None, {}

  return reply_messages
