import typing
import json
from collections.abc import Sequence
from linebot.models import CarouselColumn, CarouselTemplate, TemplateSendMessage, PostbackAction
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
        PostbackAction(label="檢視", display_text="檢視", data=json.dumps({ 'action': 'VIEW_BOOKING', 'booking_id': match.booking_id })),
        PostbackAction(label="更改", display_text="更改", data=json.dumps({ 'action': 'EDIT_BOOKING', 'booking_id': match.booking_id }))
      ]
    )
    columns.append(column)

  # Create the CarouselTemplate and send it as a message
  carousel_template = CarouselTemplate(columns=columns)
  return TemplateSendMessage(alt_text="Booking Info List", template=carousel_template)
