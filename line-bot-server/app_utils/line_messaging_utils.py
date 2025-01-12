import typing
import json
from collections.abc import Sequence
from linebot.models import CarouselColumn, CarouselTemplate, TemplateSendMessage, PostbackAction, QuickReplyButton, MessageAction, DatetimePickerAction
from const.booking_const import BOOKING_STATUS_MARK
from app_const import line_config
from utils.data_access.data_class.booking_info import BookingInfo
from utils.data_access.data_class.closure_info import ClosureInfo
from utils.booking_utils import format_booking_info
from utils.closure_utils import format_closure_info


def generate_booking_carousel_message(matches: typing.Optional[Sequence[BookingInfo]]=None):
  columns = []

  # Iterate over each match and create a carousel column
  for match in matches:
    status_mark = BOOKING_STATUS_MARK[match.status] if match.status in BOOKING_STATUS_MARK else ''
    actions=[
      MessageAction(label="更改", text=line_config.USER_COMMAND_EDIT_BOOKING.format(booking_id=match.booking_id), inputOption="closeRichMenu"),
      PostbackAction(label="已付訂金", display_text=f"訂單 {match.booking_id} 已付訂金", data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_PREPAID_BOOKING, 'booking_id': match.booking_id }), inputOption="closeRichMenu")
    ]

    if match.status != 'canceled':
      actions.append(PostbackAction(label="取消", display_text=f"取消訂單 {match.booking_id}", data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_CANCEL_BOOKING, 'booking_id': match.booking_id }), inputOption="closeRichMenu"))
    else:
      actions.append(PostbackAction(label="復原", display_text=f"復原訂單 {match.booking_id}", data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_RESTORE_BOOKING, 'booking_id': match.booking_id }), inputOption="closeRichMenu"))

    column = CarouselColumn(
      title=f"{status_mark}{match.customer_name}，{match.room_ids}，{int(match.total_price)}",
      text=format_booking_info(match, 'carousel'),
      default_action=PostbackAction(label="檢視", display_text=f"檢視訂單 {match.booking_id}", data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_VIEW_FULL_BOOKING_INFO, 'booking_id': match.booking_id })),
      actions=actions
    )
    columns.append(column)

  # Create the CarouselTemplate and send it as a message
  carousel_template = CarouselTemplate(columns=columns)
  return TemplateSendMessage(alt_text="Booking Info List", template=carousel_template)

def generate_closure_carousel_message(matches: typing.Optional[Sequence[ClosureInfo]]=None):
  columns = []

  # Iterate over each match and create a carousel column
  for match in matches:
    actions=[
      PostbackAction(label="取消關房", display_text=f"取消關房 {match.start_date}", data=json.dumps({ 'command': line_config.POSTBACK_COMMAND_CANCEL_CLOSURE, 'closure_id': match.closure_id }), inputOption="closeRichMenu"),
    ]

    column = CarouselColumn(
      text=format_closure_info(match),
      actions=actions
    )
    columns.append(column)

  # Create the CarouselTemplate and send it as a message
  carousel_template = CarouselTemplate(columns=columns)
  return TemplateSendMessage(alt_text="Closure Info List", template=carousel_template)

def generate_edit_booking_select_attribute_quick_reply_buttons():
  return [
    QuickReplyButton(action=MessageAction(label=command, text=command)) for command in [
      line_config.USER_COMMAND_EDIT_BOOKING__EDIT_CUSTOMER_NAME,
      line_config.USER_COMMAND_EDIT_BOOKING__EDIT_PHONE_NUMBER,
      line_config.USER_COMMAND_EDIT_BOOKING__EDIT_DATES,
      line_config.USER_COMMAND_EDIT_BOOKING__EDIT_ROOMS,
      line_config.USER_COMMAND_EDIT_BOOKING__EDIT_TOTAL_PRICE,
      line_config.USER_COMMAND_EDIT_BOOKING__EDIT_PREPAYMENT,
      line_config.USER_COMMAND_EDIT_BOOKING__EDIT_SOURCE,
      line_config.USER_COMMAND_EDIT_BOOKING__EDIT_NOTES,
    ]
  ]


def generate_go_to_previous_step_button():
  return QuickReplyButton(action=MessageAction(
    label=line_config.USER_COMMAND_GO_TO_PREVIOUS_STEP_OF_CURRENT_FLOW,
    text=line_config.USER_COMMAND_GO_TO_PREVIOUS_STEP_OF_CURRENT_FLOW)
  )
