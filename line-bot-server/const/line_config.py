import os

# LINE messaging API
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# User commands
USER_COMMAND_SEARCH_BOOKING_BY_KEYWORD = '查詢訂單'
USER_COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE = '查詢{date}入住的訂單'
USER_COMMAND_SEARCH_BOOKING_CHECK_IN_TODAY = '今天入住'
USER_COMMAND_SEARCH_BOOKING_CHECK_OUT_TODAY = '今天退房'
USER_COMMAND_SEARCH_BOOKING_CHECK_IN_TOMORROW = '明天入住'
USER_COMMAND_SEARCH_BOOKING_CHECK_IN_THIS_SATURDAY = '這週六入住'
USER_COMMAND_SEARCH_BOOKING_CHECK_IN_LAST_SATURDAY = '上週六入住'

# Postback commands
POSTBACK_COMMAND_SEARCH_BOOKING_BY_CHECK_IN_DATE = 'POSTBACK.SEARCH_BOOKING_BY_CHECK_IN_DATE'
POSTBACK_COMMAND_VIEW_FULL_BOOKING_INFO = 'POSTBACK.VIEW_FULL_BOOKING_INFO'
POSTBACK_COMMAND_EDIT_BOOKING = 'POSTBACK.EDIT_BOOKING'
POSTBACK_COMMAND_CANCEL_BOOKING = 'POSTBACK.CANCEL_BOOKING'
