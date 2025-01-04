import json
from datetime import datetime, timedelta
from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction, DatetimePickerAction
from app_const import line_config
from utils.data_access.data_class.closure_info import ClosureInfo
from utils.data_access.booking_dao import BookingDAO
from utils.closure_utils import format_closure_info
from utils.input_utils import is_valid_date, is_valid_num_nights
from app_utils.line_messaging_utils import generate_go_to_previous_step_button

PREVIOUS_STEP = {
  line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_NUM_NIGHTS: line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_START_DATE,
  line_config.USER_FLOW_STEP_CREATE_CLOSURE__SELECT_ROOMS: line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_START_DATE,
  line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_REASON: line_config.USER_FLOW_STEP_CREATE_CLOSURE__SELECT_ROOMS,
  line_config.USER_FLOW_STEP_CREATE_CLOSURE__CONFIRM: line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_REASON,
}

def handle_create_closure_messages(user_message: str, session: dict, booking_dao: BookingDAO):
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
    else:
      session['flow'], session['step'], session['data'] = None, None, {}
      reply_messages.append(TextSendMessage(text="已取消"))
      return reply_messages

  if session['step'] == line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_START_DATE:
    if is_previous_step or not is_valid_date(user_message):
      quick_reply_buttons.append(
        QuickReplyButton(action=DatetimePickerAction(
          label="選擇日期",
          data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_CREATE_CLOSURE__SELECT_START_DATE }),
          mode="date")
        )
      )
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新選擇關房日期:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['start_date'] = datetime.strptime(user_message, '%Y-%m-%d')
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_CLOSURE__SELECT_NUM_NIGHTS_1,
          text='1')
        ),
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_CLOSURE__SELECT_NUM_NIGHTS_2,
          text='2')
        ),
      ]
      reply_messages.append(TextSendMessage(text="請輸入關房晚數:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_NUM_NIGHTS

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_NUM_NIGHTS:
    if not is_valid_num_nights(user_message):
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_CLOSURE__SELECT_NUM_NIGHTS_1,
          text='1')
        ),
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_CLOSURE__SELECT_NUM_NIGHTS_2,
          text='2')
        ),
      ]
      reply_messages.append(TextSendMessage(text="輸入格式有誤，請重新輸入關房晚數(1~15):", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['num_nights'] = int(user_message)
      session['data']['last_date'] = session['data']['start_date'] + timedelta(days=session['data']['num_nights'] - 1)
      session['data']['room_ids'] = []
      available_room_ids = booking_dao.get_available_room_ids(session['data']['start_date'], session['data']['last_date'])
      quick_reply_buttons += [
        QuickReplyButton(action=MessageAction(
          label=room_id,
          text=room_id)
        ) for room_id in available_room_ids
      ]
      reply_messages.append(TextSendMessage(text="請選擇關閉房間:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_CLOSURE__SELECT_ROOMS

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_CLOSURE__SELECT_ROOMS:
    if user_message != line_config.USER_COMMAND_CREATE_CLOSURE__SELECT_ROOMS_FINISH:
      valid_room_ids = booking_dao.get_all_room_ids()
      available_room_ids = booking_dao.get_available_room_ids(session['data']['start_date'], session['data']['last_date'])
      available_room_ids = [room_id for room_id in available_room_ids if room_id not in session['data']['room_ids']]
      if is_previous_step or user_message not in valid_room_ids or user_message in session['data']['room_ids']:
        quick_reply_buttons += [
          QuickReplyButton(action=MessageAction(
            label=room_id,
            text=room_id)
          ) for room_id in available_room_ids
        ]
        reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請選擇關閉房間:\n(已選[{''.join(session['data']['room_ids'])}])", quick_reply=QuickReply(items=quick_reply_buttons)))
      else:
        session['data']['room_ids'].append(user_message)
        quick_reply_buttons.append(
          QuickReplyButton(action=MessageAction(
            label=line_config.USER_COMMAND_CREATE_CLOSURE__SELECT_ROOMS_FINISH,
            text=line_config.USER_COMMAND_CREATE_CLOSURE__SELECT_ROOMS_FINISH)
          )
        )
        quick_reply_buttons += [
          QuickReplyButton(action=MessageAction(
            label=room_id,
            text=room_id)
          ) for room_id in available_room_ids if room_id != user_message
        ]
        reply_messages.append(TextSendMessage(text=f"請選擇關閉房間:\n(已選[{''.join(session['data']['room_ids'])}])", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_CLOSURE__GET_REASON_FINISH,
          text=line_config.USER_COMMAND_CREATE_CLOSURE__GET_REASON_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text="請輸入原因:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_REASON

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_CLOSURE__GET_REASON:
    if is_previous_step:
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_CLOSURE__GET_REASON_FINISH,
          text=line_config.USER_COMMAND_CREATE_CLOSURE__GET_REASON_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text="請輸入原因:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['reason'] = '' if user_message == line_config.USER_COMMAND_CREATE_CLOSURE__GET_REASON_FINISH else user_message
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_CLOSURE__CONFIRM_FINISH,
          text=line_config.USER_COMMAND_CREATE_CLOSURE__CONFIRM_FINISH)
        )
      )
      closure_info = ClosureInfo(
        closure_id=-1,
        start_date=session['data']['start_date'],
        last_date=session['data']['last_date'],
        reason=session['data']['reason'],
        room_ids=''.join(session['data']['room_ids']),
      )
      closure_info_preview_text = format_closure_info(closure_info)
      reply_messages.append(TextSendMessage(text=f"請確認關房資訊:"))
      reply_messages.append(TextSendMessage(text=closure_info_preview_text, quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_CREATE_CLOSURE__CONFIRM

  elif session['step'] == line_config.USER_FLOW_STEP_CREATE_CLOSURE__CONFIRM:
    if user_message != line_config.USER_COMMAND_CREATE_CLOSURE__CONFIRM_FINISH:
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_CREATE_CLOSURE__CONFIRM_FINISH,
          text=line_config.USER_COMMAND_CREATE_CLOSURE__CONFIRM_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text=f"是否確認關房？請點擊確認或取消", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      closure_info = ClosureInfo(
        closure_id=-1,
        start_date=session['data']['start_date'],
        last_date=session['data']['last_date'],
        reason=session['data']['reason'],
        room_ids=''.join(session['data']['room_ids']),
      )
      closure_id = booking_dao.insert_closure(closure_info)
      if (closure_id):
        reply_messages.append(TextSendMessage(text=f"已關房"))
      else:
        reply_messages.append(TextSendMessage(text=f"發生錯誤，未關房"))

      # clear session data
      session['flow'], session['step'], session['data'] = None, None, {}

  return reply_messages
