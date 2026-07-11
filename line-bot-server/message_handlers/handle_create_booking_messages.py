import json
from datetime import datetime, timedelta
from urllib.parse import quote
from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction, DatetimePickerAction, URIAction
from const.booking_const import VALID_BOOKING_SOURCES
from const import line_config, property_config
from const.notification_templates import ASK_FOR_PREPAYMENT
from utils.data_access.data_class.booking_info import BookingInfo
from utils.data_access.booking_dao import BookingDAO
from utils.booking_utils import format_booking_info, get_prepayment_estimation, get_booking_room_brief, is_generic_name
from utils.input_utils import is_valid_date, is_valid_phone_number, is_valid_num_nights, is_valid_price, is_valid_extra_bed_count, format_phone_number, format_phone_number_for_display
from utils.line_messaging_utils import append_total_price_quick_reply_buttons, generate_go_to_previous_step_button

PREVIOUS_STEP = {
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PHONE_NUMBER: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CUSTOMER_NAME,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CHECK_IN_DATE: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PHONE_NUMBER,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NUM_NIGHTS: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CHECK_IN_DATE,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_ROOMS: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_CHECK_IN_DATE,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_EXTRA_BED_ROOM: line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_ROOMS,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_EXTRA_BED_COUNT: line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_EXTRA_BED_ROOM,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_TOTAL_PRICE: line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_EXTRA_BED_ROOM,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PREPAYMENT: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_TOTAL_PRICE,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_SOURCE: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PREPAYMENT,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NOTES: line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_SOURCE,
  line_config.USER_FLOW_STEP_CREATE_BOOKING__CONFIRM: line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NOTES,
}

def append_customer_phone_quick_reply(quick_reply_buttons, customer_name, booking_dao):
  if is_generic_name(customer_name):
    return

  customer = booking_dao.get_customer_by_name(customer_name)
  if customer and customer.phone_number:
    quick_reply_buttons.append(
      QuickReplyButton(action=MessageAction(
        label=customer.phone_number,
        text=customer.phone_number)
      )
    )

def append_extra_bed_count_quick_reply_buttons(quick_reply_buttons, max_extra_bed_count):
  for extra_bed_count in range(1, max_extra_bed_count + 1):
    quick_reply_buttons.append(
      QuickReplyButton(action=MessageAction(
        label=f"加{extra_bed_count}床",
        text=str(extra_bed_count))
      )
    )

def get_extra_bed_room_options(session, booking_dao):
  room_ids = session['data']['room_ids']
  selected_extra_bed_room_ids = session['data'].get('extra_bed_counts', {}).keys()
  rooms_by_id = {
    room['room_id']: room
    for room in booking_dao.get_rooms_by_ids(room_ids)
  }
  return [
    room_id
    for room_id in room_ids
    if rooms_by_id[room_id]['extra_bed_number'] > 0 and room_id not in selected_extra_bed_room_ids
  ]

def append_extra_bed_room_quick_reply_buttons(quick_reply_buttons, session, booking_dao):
  continue_command = (
    line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_EXTRA_BED_FINISH
    if session['data'].get('extra_bed_counts')
    else line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_EXTRA_BED_COUNT_0
  )
  quick_reply_buttons.append(
    QuickReplyButton(action=MessageAction(
      label=continue_command,
      text=continue_command)
    )
  )
  for room_id in get_extra_bed_room_options(session, booking_dao):
    quick_reply_buttons.append(
      QuickReplyButton(action=MessageAction(
        label=room_id,
        text=room_id)
      )
    )

def get_current_extra_bed_room_id(session):
  return session['data']['extra_bed_room_id']

def append_total_price_question(reply_messages, quick_reply_buttons, session, booking_dao):
  estimated_total_price = booking_dao.get_total_price_estimation(
    session['data']['room_ids'],
    session['data']['check_in_date'],
    session['data']['last_date'],
    sum(session['data'].get('extra_bed_counts', {}).values())
  )
  append_total_price_quick_reply_buttons(quick_reply_buttons, estimated_total_price)
  reply_messages.append(TextSendMessage(text="請輸入總金額:", quick_reply=QuickReply(items=quick_reply_buttons)))
  session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_TOTAL_PRICE

def handle_create_booking_messages(user_message: str, session: dict, booking_dao: BookingDAO):
  reply_messages = []
  quick_reply_buttons = [
    generate_go_to_previous_step_button()
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
        session['data']['extra_bed_counts'] = {}
      if session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_EXTRA_BED_ROOM:
        session['data'].pop('extra_bed_room_id', None)
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
      append_customer_phone_quick_reply(quick_reply_buttons, user_message, booking_dao)
      reply_messages.append(TextSendMessage(text="請輸入顧客電話:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PHONE_NUMBER

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_PHONE_NUMBER:
    if is_previous_step or not is_valid_phone_number(user_message):
      if 'customer_name' in session['data']:
        append_customer_phone_quick_reply(quick_reply_buttons, session['data']['customer_name'], booking_dao)
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新輸入顧客電話:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['phone_number'] = format_phone_number(user_message)
      customer = booking_dao.get_customer_by_phone_number(session['data']['phone_number'])
      if (
        customer and
        is_generic_name(session['data']['customer_name']) and
        not is_generic_name(customer.name)
      ):
        session['data']['customer_name'] = customer.name
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
      session['data']['check_in_date'] = datetime.strptime(user_message, '%Y-%m-%d').date()
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
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NUM_NIGHTS

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NUM_NIGHTS:
    if not is_valid_num_nights(user_message):
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
    if user_message != line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_ROOMS_FINISH:
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
      if not session['data']['room_ids']:
        reply_messages.append(TextSendMessage(text="請至少選擇一間房間"))
        return reply_messages
      session['data']['extra_bed_counts'] = {}
      append_extra_bed_room_quick_reply_buttons(quick_reply_buttons, session, booking_dao)
      reply_messages.append(TextSendMessage(text="請選擇要加床的房間", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_EXTRA_BED_ROOM

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_EXTRA_BED_ROOM:
    if is_previous_step:
      append_extra_bed_room_quick_reply_buttons(quick_reply_buttons, session, booking_dao)
      reply_messages.append(TextSendMessage(text="請選擇要加床的房間", quick_reply=QuickReply(items=quick_reply_buttons)))
    elif (
      user_message == line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_EXTRA_BED_COUNT_0 or
      user_message == line_config.USER_COMMAND_UPDATE_BOOKING__SELECT_EXTRA_BED_FINISH
    ):
      append_total_price_question(reply_messages, quick_reply_buttons, session, booking_dao)
    elif user_message in get_extra_bed_room_options(session, booking_dao):
      session['data']['extra_bed_room_id'] = user_message
      max_extra_bed_count = booking_dao.get_rooms_by_ids([user_message])[0]['extra_bed_number']
      append_extra_bed_count_quick_reply_buttons(quick_reply_buttons, max_extra_bed_count)
      reply_messages.append(TextSendMessage(text="加床數：", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_EXTRA_BED_COUNT
    else:
      append_extra_bed_room_quick_reply_buttons(quick_reply_buttons, session, booking_dao)
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請選擇要加床的房間", quick_reply=QuickReply(items=quick_reply_buttons)))

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_EXTRA_BED_COUNT:
    room_id = get_current_extra_bed_room_id(session)
    max_extra_bed_count = booking_dao.get_rooms_by_ids([room_id])[0]['extra_bed_number']
    if is_previous_step:
      append_extra_bed_room_quick_reply_buttons(quick_reply_buttons, session, booking_dao)
      reply_messages.append(TextSendMessage(text="請選擇要加床的房間", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_EXTRA_BED_ROOM
    elif not is_valid_extra_bed_count(user_message, max_extra_bed_count) or int(user_message) < 1:
      append_extra_bed_count_quick_reply_buttons(quick_reply_buttons, max_extra_bed_count)
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新輸入加床數：", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['extra_bed_counts'][room_id] = int(user_message)
      session['data'].pop('extra_bed_room_id', None)
      append_extra_bed_room_quick_reply_buttons(quick_reply_buttons, session, booking_dao)
      reply_messages.append(TextSendMessage(text="請選擇要加床的房間", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__SELECT_EXTRA_BED_ROOM

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_TOTAL_PRICE:
    if is_previous_step or not is_valid_price(user_message):
      estimated_total_price = booking_dao.get_total_price_estimation(
        session['data']['room_ids'],
        session['data']['check_in_date'],
        session['data']['last_date'],
        sum(session['data'].get('extra_bed_counts', {}).values())
      )
      append_total_price_quick_reply_buttons(quick_reply_buttons, estimated_total_price)
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新輸入總金額(0~100000):", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['total_price'] = int(user_message)
      estimated_prepayment = get_prepayment_estimation(session['data']['total_price'])
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
      estimated_prepayment = get_prepayment_estimation(session['data']['total_price'])
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
          label=line_config.USER_COMMAND_UPDATE_BOOKING__GET_NOTES_FINISH,
          text=line_config.USER_COMMAND_UPDATE_BOOKING__GET_NOTES_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text="請輸入備註:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NOTES

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__GET_NOTES:
    if is_previous_step:
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_UPDATE_BOOKING__GET_NOTES_FINISH,
          text=line_config.USER_COMMAND_UPDATE_BOOKING__GET_NOTES_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text="請輸入備註:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['notes'] = '' if user_message == line_config.USER_COMMAND_UPDATE_BOOKING__GET_NOTES_FINISH else user_message
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_UPDATE_BOOKING__CONFIRM_FINISH,
          text=line_config.USER_COMMAND_UPDATE_BOOKING__CONFIRM_FINISH)
        )
      )
      booking_info = BookingInfo(
        booking_id=booking_dao.get_next_booking_id(),
        status=('new' if session['data']['prepayment'] else 'prepaid'),
        customer_name=session['data']['customer_name'],
        phone_number=session['data']['phone_number'],
        check_in_date=session['data']['check_in_date'],
        last_date=session['data']['last_date'],
        total_price=session['data']['total_price'],
        notes=session['data']['notes'],
        source=session['data']['source'],
        prepayment=session['data']['prepayment'],
        prepayment_note='',
        prepayment_status=('unpaid' if session['data']['prepayment'] else 'paid'),
        room_ids=''.join(session['data']['room_ids']),
        extra_bed_counts=session['data'].get('extra_bed_counts', {})
      )
      booking_info_preview_text = format_booking_info(booking_info, 'normal')
      reply_messages.append(TextSendMessage(text=f"請確認訂單資訊:"))
      reply_messages.append(TextSendMessage(text=booking_info_preview_text, quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_BOOKING__CONFIRM

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_BOOKING__CONFIRM:
    if user_message != line_config.USER_COMMAND_UPDATE_BOOKING__CONFIRM_FINISH:
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_UPDATE_BOOKING__CONFIRM_FINISH,
          text=line_config.USER_COMMAND_UPDATE_BOOKING__CONFIRM_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text=f"是否確認新增訂單？請點擊確認或取消", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      booking_info = BookingInfo(
        booking_id=booking_dao.get_next_booking_id(),
        status=('new' if session['data']['prepayment'] else 'prepaid'),
        customer_name=session['data']['customer_name'],
        phone_number=session['data']['phone_number'],
        check_in_date=session['data']['check_in_date'],
        last_date=session['data']['last_date'],
        total_price=session['data']['total_price'],
        notes=session['data']['notes'],
        source=session['data']['source'],
        prepayment=session['data']['prepayment'],
        prepayment_note='',
        prepayment_status=('unpaid' if session['data']['prepayment'] else 'paid'),
        room_ids=''.join(session['data']['room_ids']),
        extra_bed_counts=session['data'].get('extra_bed_counts', {})
      )
      booking_id = booking_dao.upsert_booking(booking_info)
      reply_messages.append(TextSendMessage(text=f"訂單已新增完成, ID:{booking_id}"))
      if booking_info.prepayment > 0 and booking_info.prepayment_status == 'unpaid':
        room_type_summary = booking_dao.get_booking_room_type_summary(booking_info.booking_id)
        room_brief = get_booking_room_brief(room_type_summary, booking_info.extra_bed_count)
        sms_body = ASK_FOR_PREPAYMENT.format(
          property_name=property_config.PROPERTY_NAME,
          check_in_date=booking_info.check_in_date.strftime('%m/%d'),
          nights=session['data']['num_nights'],
          room_brief=room_brief,
          total_price=booking_info.total_price,
          prepayment=booking_info.prepayment,
          bank_account_info=property_config.BANK_ACCOUNT_INFO
        ).strip()
        sms_url = f"sms:{format_phone_number_for_display(booking_info.phone_number)}?body={quote(sms_body)}"

        reply_messages.append(TextSendMessage(text="匯款訊息："))
        reply_messages.append(TextSendMessage(text=sms_body))
        if booking_info.source == '自洽':
          reply_messages.append(TextSendMessage(text=f"發送簡訊：\n\n{sms_url}"))

      # clear session data
      session['flow'], session['step'], session['data'] = None, None, {}

  return reply_messages
