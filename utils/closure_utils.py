import typing
from utils.data_access.data_class.closure_info import ClosureInfo

# Function to format the booking info as per the required format
def format_closure_info(closure_info: typing.Optional[ClosureInfo]=None, variant='normal'):
  if not closure_info:
    return None

  # Format the response message
  message = ""
  if variant == 'calendar':
    message = (
      f"ＣＬＩＤ：{closure_info.closure_id}\n"
      f"原因：{closure_info.reason}\n"
    )
  else:
    message = (
      f"[關房]\n"
      f"開始日期：{closure_info.start_date.strftime('%Y/%m/%d')}\n"
      f"結束日期：{closure_info.last_date.strftime('%Y/%m/%d')}\n"
      f"房間：{closure_info.room_ids}\n"
      f"原因：{closure_info.reason}"
    )

  return message
