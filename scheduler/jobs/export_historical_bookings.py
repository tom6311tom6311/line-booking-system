import os
import logging
from datetime import datetime
from const import db_config
from utils.data_access.booking_dao import BookingDAO
from utils.booking_utils import format_booking_info

# DB Connection details
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

SORTED_BOOKINGS_FILE_PATH = './data/sorted_bookings_exported.txt'


def export_historical_bookings():
  """
  Fetch all booking information from the database, sort it by booking ID, and write to a file.
  """
  try:
    booking_dao = BookingDAO.get_instance(db_config, logging, enable_notification=False)

    # Fetch all bookings
    all_booking_infos = booking_dao.get_latest_bookings(datetime.date(1970, 1, 1))

    # Prepare content for writing to the file
    lines = []
    for booking_info in all_booking_infos:
      lines.append(format_booking_info(booking_info))
      lines.append('\n\n')

    # Write to the file
    with open(SORTED_BOOKINGS_FILE_PATH, 'w', encoding='utf-8') as f:
        f.writelines('\n'.join(lines))
    logging.info(f"Exported {len(all_booking_infos)} bookings to {SORTED_BOOKINGS_FILE_PATH}")

  except Exception as e:
      logging.error(f"Error exporting historical bookings: {e}")
