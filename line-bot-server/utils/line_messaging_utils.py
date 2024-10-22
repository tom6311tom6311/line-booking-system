import typing
import json
from collections.abc import Sequence
from linebot.models import CarouselColumn, CarouselTemplate, TemplateSendMessage, PostbackAction
from const.line_config import POSTBACK_COMMAND_VIEW_FULL_BOOKING_INFO, POSTBACK_COMMAND_EDIT_BOOKING, POSTBACK_COMMAND_CANCEL_BOOKING
from data_access.data_class.booking_info import BookingInfo
from utils.booking_utils import format_booking_info


def create_booking_carousel_message(matches: typing.Optional[Sequence[BookingInfo]]=None):
  columns = []

  # Iterate over each match and create a carousel column
  for match in matches:
    column = CarouselColumn(
      title=f"ID: {match.booking_id}",
      text=format_booking_info(match, 'carousel'),
      actions=[
        PostbackAction(label="檢視", display_text=f"檢視訂單{match.booking_id}", data=json.dumps({ 'command': POSTBACK_COMMAND_VIEW_FULL_BOOKING_INFO, 'booking_id': match.booking_id }), inputOption="closeRichMenu"),
        PostbackAction(label="更改", display_text=f"更改訂單{match.booking_id}", data=json.dumps({ 'command': POSTBACK_COMMAND_EDIT_BOOKING, 'booking_id': match.booking_id }), inputOption="closeRichMenu"),
        PostbackAction(label="取消", display_text=f"取消訂單{match.booking_id}", data=json.dumps({ 'command': POSTBACK_COMMAND_CANCEL_BOOKING, 'booking_id': match.booking_id }), inputOption="closeRichMenu")
      ]
    )
    columns.append(column)

  # Create the CarouselTemplate and send it as a message
  carousel_template = CarouselTemplate(columns=columns)
  return TemplateSendMessage(alt_text="Booking Info List", template=carousel_template)
