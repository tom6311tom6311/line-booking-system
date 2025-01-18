import os
import logging
from typing import List
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from const import db_config
from utils.booking_utils import format_booking_info
from utils.data_access.booking_dao import BookingDAO
from utils.data_access.data_class.booking_info import BookingInfo

SCOPES = ["https://www.googleapis.com/auth/calendar"]
GOOGLE_SERVICE_ACCOUNT_CRED_FILE=os.getenv('GOOGLE_SERVICE_ACCOUNT_CRED_FILE')
GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')
GOOGLE_CALENDAR_SYNC_MIN_TIME = datetime.strptime(os.getenv('GOOGLE_CALENDAR_SYNC_MIN_TIME'), '%Y-%m-%dT%H:%M:%S')

# Task to load latest bookings and sync to Google Calendar
def sync_bookings_to_google_calendar():
  booking_dao = BookingDAO.get_instance(db_config, logging)
  latest_sync_time = booking_dao.get_latest_sync_time(sync_type="sql_to_google_calendar")
  if latest_sync_time < GOOGLE_CALENDAR_SYNC_MIN_TIME:
    latest_sync_time = GOOGLE_CALENDAR_SYNC_MIN_TIME
  latest_bookings = booking_dao.get_latest_bookings(latest_sync_time)
  if not latest_bookings:
    logging.info("No new bookings to sync.")
    return

  success = True
  try:
    write_bookings_to_google_calendar(latest_bookings)
  except Exception as e:
    success = False
    logging.error(f"Sync to Google Calendar failed: {e}")

  synced_booking_ids = [booking_info.booking_id for booking_info in latest_bookings]
  booking_dao.log_sync_record("sql_to_google_calendar", synced_booking_ids, success)

# Util function to write bookings to Google Calendar
def write_bookings_to_google_calendar(bookings: List[BookingInfo]):
    service = build_google_calendar_service()
    for booking_info in bookings:
      try:
        # Event details for either creating or updating the event
        event_body = {
          'summary': f'{booking_info.customer_name}，{booking_info.room_ids}，{int(booking_info.total_price)}',
          'description': format_booking_info(booking_info, 'calendar'),
          'start': {
            'date': booking_info.check_in_date.strftime('%Y-%m-%d'),
            'timeZone': 'Asia/Taipei',
          },
          'end': {
            'date': (booking_info.last_date).strftime('%Y-%m-%d'),
            'timeZone': 'Asia/Taipei',
          },
          'reminders': {
            'useDefault': False,
            'overrides': [
              {'method': 'popup', 'minutes': 1440},  # Reminder 1 day before
            ],
          },
        }

        # Check if the event with the same booking_id already exists
        existing_events = []
        events_result = service.events().list(
          calendarId=GOOGLE_CALENDAR_ID,
          q=f"ＩＤ：{booking_info.booking_id}",
          singleEvents=True
        ).execute()

        for event in events_result.get('items', []):
          if f"ＩＤ：{booking_info.booking_id}" in event.get('description', ''):
            existing_events.append(event)

        if booking_info.status == 'canceled':
          if not existing_events:
            logging.info(f"No existing event found to delete for canceled booking ID {booking_info.booking_id}")
          else:
            for existing_event in existing_events:
              # Delete the event if booking is canceled and event exists
              service.events().delete(
                  calendarId=GOOGLE_CALENDAR_ID,
                  eventId=existing_event['id']
              ).execute()
              logging.info(f"Deleted Google Calendar event for canceled booking ID {booking_info.booking_id}")
        else:
          # If booking is not canceled, create or update the event
          if len(existing_events) > 1:
            # Somehow there are duplicated events. Reduce them to only 1
            for existing_event in existing_events[:-1]:
              service.events().delete(
                  calendarId=GOOGLE_CALENDAR_ID,
                  eventId=existing_event['id']
              ).execute()
              logging.info(f"Deleted duplicated Google Calendar event for booking ID {booking_info.booking_id}")
          if existing_events:
            # Update the existing event
            service.events().update(
              calendarId=GOOGLE_CALENDAR_ID,
              eventId=existing_events[-1]['id'],
              body=event_body
            ).execute()
            logging.info(f"Updated Google Calendar event for booking ID {booking_info.booking_id}")
          else:
            # Insert new event
            service.events().insert(
              calendarId=GOOGLE_CALENDAR_ID,
              body=event_body
            ).execute()
            logging.info(f"Created new Google Calendar event for booking ID {booking_info.booking_id}")

      except Exception as e:
        logging.error(f"Error syncing booking {booking_info.booking_id} to Google Calendar: {e}")
        raise e

# Util function to build a connection to google calendar API
def build_google_calendar_service():
  creds = Credentials.from_service_account_file(GOOGLE_SERVICE_ACCOUNT_CRED_FILE, scopes=SCOPES)
  service = build('calendar', 'v3', credentials=creds)
  return service
