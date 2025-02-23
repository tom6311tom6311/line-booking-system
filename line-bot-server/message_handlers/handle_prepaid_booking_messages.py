from linebot.models import TextSendMessage,  QuickReply, QuickReplyButton, MessageAction
from const import line_config
from utils.data_access.booking_dao import BookingDAO
from utils.input_utils import is_valid_price
from utils.line_messaging_utils import generate_go_to_previous_step_button

PREVIOUS_STEP = {
  line_config.USER_FLOW_STEP_PREPAID_BOOKING__GET_PREPAYMENT_NOTE: line_config.USER_FLOW_STEP_PREPAID_BOOKING__GET_PREPAYMENT_AMOUNT,
  line_config.USER_FLOW_STEP_PREPAID_BOOKING__CONFIRM: line_config.USER_FLOW_STEP_PREPAID_BOOKING__GET_PREPAYMENT_NOTE,
}

def handle_prepaid_booking_messages(user_message: str, session: dict, booking_dao: BookingDAO):
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
    else:
      session['flow'], session['step'], session['data'] = None, None, {}
      reply_messages.append(TextSendMessage(text="已取消"))
      return reply_messages

  if session['step'] == line_config.USER_FLOW_STEP_PREPAID_BOOKING__GET_PREPAYMENT_AMOUNT:
    if is_previous_step or not is_valid_price(user_message):
      booking_info = booking_dao.get_booking_info(session['data']['booking_id'])
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
      reply_messages.append(TextSendMessage(text=f"{'' if is_previous_step else '輸入格式有誤，'}請重新輸入已付訂金金額:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['prepayment'] = int(user_message)
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_PREPAID_BOOKING__GET_PREPAYMENT_NOTE_FINISH,
          text=line_config.USER_COMMAND_PREPAID_BOOKING__GET_PREPAYMENT_NOTE_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text="請輸入匯款摘要:", quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_PREPAID_BOOKING__GET_PREPAYMENT_NOTE

  elif session['step'] == line_config.USER_FLOW_STEP_PREPAID_BOOKING__GET_PREPAYMENT_NOTE:
    if is_previous_step:
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_PREPAID_BOOKING__GET_PREPAYMENT_NOTE_FINISH,
          text=line_config.USER_COMMAND_PREPAID_BOOKING__GET_PREPAYMENT_NOTE_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text=f"請重新輸入匯款摘要:", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      session['data']['prepayment_note'] = '' if user_message == line_config.USER_COMMAND_PREPAID_BOOKING__GET_PREPAYMENT_NOTE_FINISH else user_message
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_PREPAID_BOOKING__CONFIRM_FINISH,
          text=line_config.USER_COMMAND_PREPAID_BOOKING__CONFIRM_FINISH)
        )
      )
      prepayment_preview_text=f"已付訂金：{session['data']['prepayment']}元\n匯款摘要：{session['data']['prepayment_note']}"
      reply_messages.append(TextSendMessage(text=f"請確認訂金資訊:"))
      reply_messages.append(TextSendMessage(text=prepayment_preview_text, quick_reply=QuickReply(items=quick_reply_buttons)))
      session['step'] = line_config.USER_FLOW_STEP_PREPAID_BOOKING__CONFIRM

  elif session['step'] == line_config.USER_FLOW_STEP_PREPAID_BOOKING__CONFIRM:
    if user_message != line_config.USER_COMMAND_PREPAID_BOOKING__CONFIRM_FINISH:
      quick_reply_buttons.append(
        QuickReplyButton(action=MessageAction(
          label=line_config.USER_COMMAND_PREPAID_BOOKING__CONFIRM_FINISH,
          text=line_config.USER_COMMAND_PREPAID_BOOKING__CONFIRM_FINISH)
        )
      )
      reply_messages.append(TextSendMessage(text=f"是否確認已付訂金？請點擊確認或取消", quick_reply=QuickReply(items=quick_reply_buttons)))
    else:
      if (booking_dao.update_booking_prepaid(session['data']['booking_id'], session['data']['prepayment'], session['data']['prepayment_note'])):
        reply_messages.append(TextSendMessage(text=f"訂金狀態已更新完成"))
      else:
        reply_messages.append(TextSendMessage(text=f"訂金狀態更新失敗"))

      # clear session data
      session['flow'], session['step'], session['data'] = None, None, {}

  return reply_messages
