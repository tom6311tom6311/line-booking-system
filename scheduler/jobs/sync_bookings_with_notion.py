import os
import logging
import pytz
from typing import List
from datetime import datetime
from const import db_config
from notion_client import Client
from utils.input_utils import format_phone_number
from utils.data_access.booking_dao import BookingDAO
from utils.data_access.data_class.booking_info import BookingInfo

NOTION_TOKEN=os.getenv('NOTION_TOKEN')
NOTION_DATABASE_ID=os.getenv('NOTION_DATABASE_ID')
NOTION_SYNC_MIN_TIME = datetime.strptime(os.getenv('NOTION_SYNC_MIN_TIME'), '%Y-%m-%d')
notion = Client(auth=NOTION_TOKEN)
local_tz = pytz.timezone('Asia/Taipei')
utc_tz = pytz.timezone('UTC')

# Task to sync latest bookings and to/from Notion
def sync_bookings_with_notion():
  booking_dao = BookingDAO.get_instance(db_config, logging)
  latest_sync_time = booking_dao.get_latest_sync_time(sync_type="sql_with_notion")
  if latest_sync_time < NOTION_SYNC_MIN_TIME:
    latest_sync_time = NOTION_SYNC_MIN_TIME
  latest_bookings_in_db = booking_dao.get_latest_bookings(latest_sync_time)
  latest_bookings_from_notion = get_latest_bookings_from_notion(latest_sync_time)

  logging.info(f"Latest bookings in db (before conflict detection): {[booking_info.booking_id for booking_info in latest_bookings_in_db]}")
  logging.info(f"Latest bookings from notion (before conflict detection): {[booking_info.booking_id for booking_info in latest_bookings_from_notion]}")

  # find conflicted bookings and keep only the more recent one
  latest_booking_ids_in_db = [booking_info.booking_id for booking_info in latest_bookings_in_db]
  latest_booking_ids_from_notion = [booking_info.booking_id for booking_info in latest_bookings_from_notion]
  booking_ids_in_db_to_skip = []
  booking_ids_from_notion_to_skip = []
  for booking_id_in_db, booking_info_in_db in zip(latest_booking_ids_in_db, latest_bookings_in_db):
    for booking_id_from_notion, booking_info_from_notion in zip(latest_booking_ids_from_notion, latest_bookings_from_notion):
      if booking_id_in_db == booking_id_from_notion:
        if booking_info_in_db.modified > booking_info_from_notion.modified:
          booking_ids_from_notion_to_skip.append(booking_id_from_notion)
        else:
          booking_ids_in_db_to_skip.append(booking_id_in_db)

  latest_bookings_in_db = [booking_info for booking_info in latest_bookings_in_db if booking_info.booking_id not in booking_ids_in_db_to_skip]
  latest_bookings_from_notion = [booking_info for booking_info in latest_bookings_from_notion if booking_info.booking_id not in booking_ids_from_notion_to_skip]

  logging.info(f"Latest bookings in db: {[booking_info.booking_id for booking_info in latest_bookings_in_db]}")
  logging.info(f"Latest bookings from notion: {[booking_info.booking_id for booking_info in latest_bookings_from_notion]}")

  success = True
  try:
    write_bookings_to_notion(latest_bookings_in_db)
    write_bookings_to_db(latest_bookings_from_notion)
  except Exception as e:
    success = False
    logging.error(f"Sync with Notion failed: {e}")

  synced_booking_ids = [booking_info.booking_id for booking_info in latest_bookings_in_db + latest_bookings_from_notion]
  booking_dao.log_sync_record("sql_with_notion", synced_booking_ids, success)

def get_latest_bookings_from_notion(latest_sync_time: datetime) -> List[BookingInfo]:
  try:
    latest_sync_time_normalized = latest_sync_time.replace(tzinfo=local_tz).astimezone(utc_tz).isoformat()
    response = notion.databases.query(
      database_id=NOTION_DATABASE_ID,
      filter={
        "timestamp": "last_edited_time",
        "last_edited_time": {"after": latest_sync_time_normalized}
      }
    )

    latest_bookings = []
    if not response['results']:
      return latest_bookings

    for entry in response['results']:
      booking_info_from_notion = load_booking_info_from_notion_entry(entry)
      if not booking_info_from_notion:
        continue
      latest_bookings.append(booking_info_from_notion)

    return latest_bookings

  except Exception as e:
    logging.error(f"Error loading latest bookings from Notion: {e}")
    return []

def load_booking_info_from_notion_entry(notion_entry: dict):
  try:
    properties = notion_entry['properties']
    booking_id = int(properties['ID']['title'][0]['text']['content'])
    customer_name = properties['姓名']['rich_text'][0]['text']['content']
    phone_number = format_phone_number(properties['電話']['phone_number'])
    check_in_date = properties['日期(不含退房日)']['date']['start']
    last_date = properties['日期(不含退房日)']['date']['end']
    room_ids = ''.join([s['name'] for s in properties['房間']['multi_select']])
    total_price = float(properties['總金額']['number'])
    source = properties['來源']['select']['name']
    prepayment = float(properties['訂金']['number'])
    prepayment_note = properties['匯款摘要']['rich_text'][0]['text']['content'] if properties['匯款摘要']['rich_text'] else ''
    prepayment_status = 'paid' if properties['已付訂金']['checkbox'] else 'unpaid'
    notes = properties['備註']['rich_text'][0]['text']['content'] if properties['備註']['rich_text'] else ''
    status = 'canceled' if properties['取消']['checkbox'] else ('prepaid' if prepayment_status == 'paid' else 'new')

    # Convert Notion dates to datetime for comparison
    created = datetime.fromisoformat(notion_entry['created_time'].replace("Z", "+00:00")).astimezone(local_tz).replace(tzinfo=None)
    modified = datetime.fromisoformat(notion_entry['last_edited_time'].replace("Z", "+00:00")).astimezone(local_tz).replace(tzinfo=None)

    return BookingInfo(
      booking_id=booking_id,
      status=status,
      customer_name=customer_name,
      phone_number=phone_number,
      check_in_date=check_in_date,
      last_date=last_date,
      total_price=total_price,
      notes=notes,
      source=source,
      prepayment=prepayment,
      prepayment_note=prepayment_note,
      prepayment_status=prepayment_status,
      room_ids=room_ids,
      created=created,
      modified=modified
    )
  except Exception as e:
    logging.error(f"Corrupted data detected. Skip loading {notion_entry}")
    return None


# Util function to write bookings to Notion
def write_bookings_to_notion(bookings: List[BookingInfo]):
  for booking_info in bookings:
    # Construct Notion page properties
    properties = {
      "ID": {
        "title": [{ "text": { "content": str(booking_info.booking_id) } }]
      },
      "姓名": {
        "rich_text": [{ "text": { "content": booking_info.customer_name } }]
      },
      "電話": {
        "phone_number": booking_info.phone_number
      },
      "日期(不含退房日)": {
        "date": {
          "start": booking_info.check_in_date.strftime('%Y-%m-%d'),
          "end": booking_info.last_date.strftime('%Y-%m-%d')
        }
      },
      "房間": {
        "multi_select": [({ "name": room_id }) for room_id in booking_info.room_ids]
      },
      "總金額": {
        "number": int(booking_info.total_price)
      },
      "來源": {
        "select": { "name": booking_info.source }
      },
      "訂金": {
        "number": int(booking_info.prepayment)
      },
      "已付訂金": {
        "checkbox": booking_info.prepayment_status == 'paid'
      },
      "匯款摘要": {
        "rich_text": [{ "text": {"content": booking_info.prepayment_note or '' } }]
      },
      "備註": {
        "rich_text": [{ "text": { "content": booking_info.notes or '' } }]
      },
      "取消": {
        "checkbox": booking_info.status == 'canceled'
      },
    }

    try:
      query = notion.databases.query(database_id=NOTION_DATABASE_ID, filter={
        "property": "ID",
        "title": {"equals": str(booking_info.booking_id)}
      })

      if query['results']:
        if len(query['results']) > 1:
          logging.warning(f"Duplicated event with ID {booking_info.booking_id} detected in Notion")

        # Update existing Notion page
        page_id = query['results'][0]['id']
        notion.pages.update(page_id=page_id, properties=properties)
        logging.info(f"Updated Notion entry for booking ID {booking_info.booking_id}")
      else:
        # Create a new Notion page
        notion.pages.create(parent={"database_id": NOTION_DATABASE_ID}, properties=properties)
        logging.info(f"Created new Notion entry for booking ID {booking_info.booking_id}")
    except Exception as e:
      logging.error(f"Error syncing booking ID {booking_info.booking_id} to Notion: {e}")
      raise e

# Util function to write bookings to DB
def write_bookings_to_db(bookings: List[BookingInfo]):
  try:
    booking_dao = BookingDAO.get_instance(db_config, logging)
    for booking_info in bookings:
      booking_id = booking_dao.upsert_booking(booking_info)
      logging.info(f"Created or updated SQL booking record {booking_id} from Notion")
      if (booking_id != booking_info.booking_id):
        logging.warning(f"Created Booking ID {booking_id} does not match Notion one {booking_info.booking_id}.")
  except Exception as e:
    logging.error(f"Error syncing from Notion to SQL: {e}")
    raise e
