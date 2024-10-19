import typing
from collections.abc import Sequence
from linebot.models import CarouselColumn, CarouselTemplate, TemplateSendMessage, TextSendMessage
from data_access.data_class.booking_info import BookingInfo
from utils.booking_utils import format_booking_info


def create_booking_carousel_message(matches: typing.Optional[Sequence[BookingInfo]]=None):
  columns = []

  # Iterate over each match and create a carousel column
  for match in matches:
    column = CarouselColumn(
      title=f"#{match.booking_id}",
      text=format_booking_info(match),
      actions=[
          TextSendMessage(label="更改", text="更改")
      ]
    )
    columns.append(column)

  # Create the CarouselTemplate and send it as a message
  carousel_template = CarouselTemplate(columns=columns)
  return TemplateSendMessage(alt_text="Booking Info List", template=carousel_template)
