import psycopg2
import psycopg2.pool
from typing import Optional
from datetime import datetime, timedelta
from utils.booking_utils import is_generic_name, is_generic_phone_number
from utils.line_notification_service import LineNotificationService
from .data_class.booking_info import BookingInfo
from .data_class.closure_info import ClosureInfo
from .data_class.customer import Customer


class BookingDAO:
  _instance = None

  def __init__(self, db_config, logger, enable_notification):
    self.db_config = db_config
    self.logger = logger
    self.enable_notification = enable_notification
    try:
      # Create a connection pool with min and max connections
      self.connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20,  # Min 1 and Max 20 connections in the pool
        user=self.db_config.DB_USER,
        password=self.db_config.DB_PASSWORD,
        host=self.db_config.DB_HOST,
        database=self.db_config.DB_NAME
      )
      if self.connection_pool:
        self.logger.info("Connection pool created successfully")

    except (Exception, psycopg2.DatabaseError) as error:
      self.logger.error(f"Error while creating the connection pool: {error}")

  @classmethod
  def get_instance(cls, db_config=None, logger=None, enable_notification=True):
    if cls._instance is None:
      cls._instance = BookingDAO(db_config, logger, enable_notification)
    return cls._instance

  def get_connection(self):
    try:
      connection = self.connection_pool.getconn()
      if connection:
        connection.autocommit = True
      return connection
    except Exception as e:
      self.logger.error(f"Error retrieving connection from pool: {e}")
      return None

  def release_connection(self, connection):
    try:
      if connection:
        self.connection_pool.putconn(connection)
    except Exception as e:
      self.logger.error(f"Error releasing connection back to the pool: {e}")

  def close_all_connections(self):
    try:
      self.connection_pool.closeall()
      self.logger.info("All connections in the pool closed")
    except Exception as e:
      self.logger.error(f"Error closing all connections in the pool: {e}")

  # Function to query the booking info by booking_id
  def get_booking_info(self, booking_id) -> Optional[BookingInfo]:
    connection = self.get_connection()
    if not connection:
      return None

    booking_info = None
    try:
      cursor = connection.cursor()
      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date,
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_note, b.prepayment_status,
        STRING_AGG(r.room_id, '' ORDER BY r.ctid) AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE b.booking_id = %s
      GROUP BY b.booking_id, c.customer_id;
      """
      cursor.execute(query, (booking_id,))
      row = cursor.fetchone()
      cursor.close()

      if (row):
        booking_info = BookingInfo(
          booking_id=row[0],
          status=row[1],
          customer_name=row[2],
          phone_number=row[3],
          check_in_date=row[4],
          last_date=row[5],
          total_price=float(row[6]),
          notes=row[7] or '',
          source=row[8],
          prepayment=float(row[9]),
          prepayment_note=row[10] or '',
          prepayment_status=row[11],
          room_ids=row[12],
          created=row[13],
          modified=row[14]
        )
    except Exception as e:
      self.logger.error(f"Error querying booking info: {e}")
    finally:
      self.release_connection(connection)
    return booking_info

  def upsert_booking(self, booking_info: BookingInfo) -> Optional[int]:
    existing_booking_info = self.get_booking_info(booking_info.booking_id)
    is_customer_changed = (
      existing_booking_info and (
        existing_booking_info.customer_name != booking_info.customer_name or
        existing_booking_info.phone_number != booking_info.phone_number
      )
    )

    # upsert customer first
    customer_id = self.upsert_customer(Customer(
      name=booking_info.customer_name,
      phone_number=booking_info.phone_number
    ))

    connection = self.get_connection()
    if not connection:
      return None

    booking_id = None
    try:
      cursor = connection.cursor()
      if existing_booking_info:
        if booking_info == existing_booking_info and not is_customer_changed:
          cursor.close()
          return existing_booking_info.booking_id
        booking_id = existing_booking_info.booking_id
        update_booking_query = """
        UPDATE Bookings
        SET customer_id = %s, status = %s, check_in_date = %s, last_date = %s,
            total_price = %s, prepayment = %s, prepayment_status = %s, source = %s, notes = %s
        WHERE booking_id = %s
        """
        cursor.execute(update_booking_query, (
          customer_id,
          booking_info.status,
          booking_info.check_in_date,
          booking_info.last_date,
          booking_info.total_price,
          booking_info.prepayment,
          booking_info.prepayment_status,
          booking_info.source,
          booking_info.notes,
          existing_booking_info.booking_id
        ))

        # Delete existing RoomBookings that relate to this booking_id
        delete_room_bookings_query = """
        DELETE FROM RoomBookings
        WHERE booking_id = %s
        """
        cursor.execute(delete_room_bookings_query, (booking_id,))
      else:
        insert_query = """
        INSERT INTO Bookings (customer_id, status, check_in_date, last_date, total_price, prepayment, prepayment_status, source, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING booking_id;
        """
        cursor.execute(insert_query, (
          customer_id,
          booking_info.status,
          booking_info.check_in_date,
          booking_info.last_date,
          booking_info.total_price,
          booking_info.prepayment,
          booking_info.prepayment_status,
          booking_info.source,
          booking_info.notes
        ))
        booking_id = cursor.fetchone()[0]

      # Insert room-booking relationships into RoomBookings table
      for room_id in booking_info.room_ids:
        insert_room_bookings_query = """
        INSERT INTO RoomBookings (booking_id, room_id)
        VALUES (%s, %s);
        """
        cursor.execute(insert_room_bookings_query, (
          booking_id,
          room_id
        ))
      cursor.close()

      if (self.enable_notification):
        if existing_booking_info:
          if (
            existing_booking_info.status != booking_info.status
          ):
            if (booking_info.status == 'canceled'):
              LineNotificationService(self.logger).notify_booking_canceled(booking_info)
            elif (existing_booking_info.status == 'canceled'):
              LineNotificationService(self.logger).notify_booking_restored(booking_info)
            elif (booking_info.status == 'prepaid'):
              LineNotificationService(self.logger).notify_booking_prepaid(booking_info)
          elif (existing_booking_info != booking_info):
            LineNotificationService(self.logger).notify_booking_updated(booking_info)
        else:
          LineNotificationService(self.logger).notify_booking_created(booking_info)

    except Exception as e:
      self.logger.error(f"Error upsert booking {booking_id}: {e}")
    finally:
      self.release_connection(connection)
    return booking_id

  def cancel_booking(self, booking_id):
    connection = self.get_connection()
    if not connection:
      return False

    existing_booking_info = self.get_booking_info(booking_id)
    if not existing_booking_info:
      self.logger.warning(f"Trying to cancel booking with ID {booking_id} but not found.")
      return False

    success = False
    try:
      cursor = connection.cursor()
      query = """
      UPDATE Bookings
      SET status = 'canceled'::booking_statuses
      WHERE booking_id = %s
      RETURNING booking_id;
      """
      cursor.execute(query, (booking_id,))
      result = cursor.fetchone()

      if result:
        success = True
        if (self.enable_notification):
          LineNotificationService(self.logger).notify_booking_canceled(existing_booking_info)
      else:
        self.logger.warning(f"Trying to cancel booking with ID {booking_id} but not found.")

    except Exception as e:
      self.logger.error(f"Error canceling booking {booking_id}: {e}")
    finally:
      self.release_connection(connection)
    return success

  def restore_booking(self, booking_id):
    connection = self.get_connection()
    if not connection:
      return False

    existing_booking_info = self.get_booking_info(booking_id)
    if not existing_booking_info:
      self.logger.warning(f"Trying to restore booking with ID {booking_id} but not found.")
      return False

    success = False
    try:
      cursor = connection.cursor()
      query = """
      UPDATE Bookings
      SET status =
        CASE
          WHEN prepayment_status = 'paid'::prepayment_statuses THEN 'prepaid'::booking_statuses
          ELSE 'new'::booking_statuses
        END
      WHERE booking_id = %s
      RETURNING booking_id;
      """
      cursor.execute(query, (booking_id,))
      result = cursor.fetchone()

      if result:
        success = True
        booking_info = self.get_booking_info(booking_id)
        if (self.enable_notification):
          LineNotificationService(self.logger).notify_booking_restored(booking_info)
      else:
        self.logger.warning(f"Trying to restore booking with ID {booking_id} but not found.")

    except Exception as e:
      self.logger.error(f"Error restoring booking {booking_id}: {e}")
    finally:
      self.release_connection(connection)
    return success

  def update_booking_prepaid(self, booking_id, prepayment, prepayment_note):
    connection = self.get_connection()
    if not connection:
      return False

    existing_booking_info = self.get_booking_info(booking_id)
    if not existing_booking_info:
      self.logger.warning(f"Trying to update the prepayment of booking with ID {booking_id} but not found.")
      return False

    success = False
    try:
      cursor = connection.cursor()
      query = """
      UPDATE Bookings
      SET status = 'prepaid'::booking_statuses, prepayment = %s, prepayment_note = %s, prepayment_status = 'paid'::prepayment_statuses
      WHERE booking_id = %s
      RETURNING booking_id;
      """
      cursor.execute(query, (prepayment, prepayment_note, booking_id))
      result = cursor.fetchone()

      if result:
        success = True
        booking_info = self.get_booking_info(booking_id)
        if (self.enable_notification):
          LineNotificationService(self.logger).notify_booking_prepaid(booking_info)
      else:
        self.logger.warning(f"Trying to update the prepayment of booking with ID {booking_id} but not found.")

    except Exception as e:
      self.logger.error(f"Error updating the prepayment of booking {booking_id}: {e}")
    finally:
      self.release_connection(connection)
    return success

  def get_next_booking_id(self):
    connection = self.get_connection()
    if not connection:
      return None

    next_id = None
    try:
      cursor = connection.cursor()
      query = "SELECT COALESCE(MAX(booking_id), 0) + 1 AS next_booking_id FROM Bookings;"
      cursor.execute(query)
      next_id = cursor.fetchone()[0]
    except Exception as e:
      self.logger.error(f"Error fetching next booking_id: {e}")
    finally:
      self.release_connection(connection)
    return next_id

  def search_booking_by_keyword(self, keyword, limit=3) -> Optional[list[BookingInfo]]:
    connection = self.get_connection()
    if not connection:
      return None

    try:
      cursor = connection.cursor()

      # SQL query to search for bookings by booking_id, phone_number, or customer_name
      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date, 
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_note, b.prepayment_status,
        STRING_AGG(r.room_id, '' ORDER BY r.ctid) AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE b.booking_id::text LIKE %s
        OR c.phone_number LIKE %s
        OR c.name LIKE %s
      GROUP BY b.booking_id, c.customer_id
      ORDER BY
        CASE
          WHEN b.status = 'canceled'::booking_statuses THEN 1
          ELSE 0
        END,
        b.booking_id DESC
      LIMIT %s;
      """

      booking_id = f"{keyword}"
      phone_number_like = f"%{keyword}"
      customer_name_like = f"%{keyword}%"
      cursor.execute(query, (booking_id, phone_number_like, customer_name_like, limit))
      rows = cursor.fetchall()
      cursor.close()

      matches = []
      for row in rows:
        booking_info = BookingInfo(
          booking_id=row[0],
          status=row[1],
          customer_name=row[2],
          phone_number=row[3],
          check_in_date=row[4],
          last_date=row[5],
          total_price=float(row[6]),
          notes=row[7] or '',
          source=row[8],
          prepayment=float(row[9]),
          prepayment_note=row[10] or '',
          prepayment_status=row[11],
          room_ids=row[12],
          created=row[13],
          modified=row[14]
        )
        matches.append(booking_info)

      return matches

    except Exception as e:
        self.logger.error(f"Error searching bookings: {e}")
        return None

    finally:
        self.release_connection(connection)

  def search_booking_by_date(self, date, mode=None, include_canceled=False) -> Optional[list[BookingInfo]]:
    connection = self.get_connection()
    if not connection:
      return None

    matches = []
    try:
      date_query = "%s BETWEEN b.check_in_date AND b.last_date"
      if mode == 'check_in_date':
        date_query = "b.check_in_date = %s"
      elif mode == 'last_date':
        date_query = "b.last_date = %s"

      cursor = connection.cursor()

      # SQL query to search for bookings by check-in date
      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date,
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_note, b.prepayment_status,
        STRING_AGG(r.room_id, '' ORDER BY r.ctid) AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE {date_query}
      GROUP BY b.booking_id, c.customer_id
      ORDER BY
        CASE
          WHEN b.status = 'canceled'::booking_statuses THEN 1
          ELSE 0
        END,
        b.booking_id;
      """

      cursor.execute(query.format(date_query=date_query), (date,))
      rows = cursor.fetchall()
      cursor.close()

      for row in rows:
        booking_info = BookingInfo(
          booking_id=row[0],
          status=row[1],
          customer_name=row[2],
          phone_number=row[3],
          check_in_date=row[4],
          last_date=row[5],
          total_price=float(row[6]),
          notes=row[7] or '',
          source=row[8],
          prepayment=float(row[9]),
          prepayment_note=row[10] or '',
          prepayment_status=row[11],
          room_ids=row[12],
          created=row[13],
          modified=row[14]
        )
        if (not include_canceled and booking_info.status == 'canceled'):
          continue
        matches.append(booking_info)

    except Exception as e:
      self.logger.error(f"Error searching bookings by check-in date: {e}")
      matches = None

    finally:
      self.release_connection(connection)

    return matches

  def search_booking_not_prepaid(self) -> Optional[list[BookingInfo]]:
    connection = self.get_connection()
    if not connection:
      return None

    matches = []
    try:
      cursor = connection.cursor()

      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date,
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_note, b.prepayment_status,
        STRING_AGG(r.room_id, '' ORDER BY r.ctid) AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE b.check_in_date >= NOW()
        AND b.status != 'canceled'::booking_statuses
        AND b.prepayment > 0 AND b.prepayment_status = 'unpaid'::prepayment_statuses
      GROUP BY b.booking_id, c.customer_id
      ORDER BY
        b.check_in_date, b.booking_id;
      """

      cursor.execute(query)
      rows = cursor.fetchall()
      cursor.close()

      for row in rows:
        booking_info = BookingInfo(
          booking_id=row[0],
          status=row[1],
          customer_name=row[2],
          phone_number=row[3],
          check_in_date=row[4],
          last_date=row[5],
          total_price=float(row[6]),
          notes=row[7] or '',
          source=row[8],
          prepayment=float(row[9]),
          prepayment_note=row[10] or '',
          prepayment_status=row[11],
          room_ids=row[12],
          created=row[13],
          modified=row[14]
        )
        matches.append(booking_info)

    except Exception as e:
      self.logger.error(f"Error searching bookings not prepaid: {e}")
      matches = None

    finally:
      self.release_connection(connection)

    return matches

  def get_bookings_by_month(self, year_month: str) -> Optional[list[BookingInfo]]:
    """
    Retrieves all bookings with a check-in date in the specified month.

    Args:
        year_month (str): The target month in 'YYYY-MM' format.

    Returns:
        List[BookingInfo]: A list of bookings within the given month.
    """
    connection = self.get_connection()
    if not connection:
      return None

    matches = []
    try:
      # Convert YYYY-MM to the first and last day of the month
      first_day = datetime.strptime(year_month, "%Y-%m").date()
      last_day = datetime(first_day.year, first_day.month + 1, 1).date() if first_day.month < 12 else datetime(first_day.year + 1, 1, 1).date()

      cursor = connection.cursor()

      # SQL query to retrieve bookings within the given month
      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date,
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_note, b.prepayment_status,
        STRING_AGG(r.room_id, '' ORDER BY r.ctid) AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE b.check_in_date >= %s AND b.check_in_date < %s
        AND b.status != 'canceled'::booking_statuses
      GROUP BY b.booking_id, c.customer_id
      ORDER BY
        b.check_in_date,
        b.booking_id;
      """
      cursor.execute(query, (first_day, last_day))
      rows = cursor.fetchall()
      cursor.close()

      for row in rows:
        booking_info = BookingInfo(
          booking_id=row[0],
          status=row[1],
          customer_name=row[2],
          phone_number=row[3],
          check_in_date=row[4],
          last_date=row[5],
          total_price=float(row[6]),
          notes=row[7] or '',
          source=row[8],
          prepayment=float(row[9]),
          prepayment_note=row[10] or '',
          prepayment_status=row[11],
          room_ids=row[12],
          created=row[13],
          modified=row[14]
        )
        matches.append(booking_info)

    except Exception as e:
      self.logger.error(f"Error getting bookings by month: {e}")
      matches = None

    finally:
      self.release_connection(connection)

    return matches

  def get_latest_bookings(self, last_sync_time) -> Optional[list[BookingInfo]]:
    connection = self.get_connection()
    if not connection:
      return None

    matches = []
    try:
      cursor = connection.cursor()

      # SQL query to get bookings created or modified after the last sync time
      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date,
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_note, b.prepayment_status,
        STRING_AGG(r.room_id, '' ORDER BY r.ctid) AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE b.created >= %s OR b.modified >= %s
      GROUP BY b.booking_id, c.customer_id
      ORDER BY b.created;
      """

      cursor.execute(query, (last_sync_time, last_sync_time))
      rows = cursor.fetchall()
      cursor.close()

      for row in rows:
        booking_info = BookingInfo(
          booking_id=row[0],
          status=row[1],
          customer_name=row[2],
          phone_number=row[3],
          check_in_date=row[4],
          last_date=row[5],
          total_price=float(row[6]),
          notes=row[7] or '',
          source=row[8],
          prepayment=float(row[9]),
          prepayment_note=row[10] or '',
          prepayment_status=row[11],
          room_ids=row[12],
          created=row[13],
          modified=row[14]
        )
        matches.append(booking_info)

    except Exception as e:
      self.logger.error(f"Error fetching latest bookings: {e}")
      matches = None

    finally:
      self.release_connection(connection)

    return matches

  ##########################################
  ### Closure data access functions  ###
  ##########################################

  # Function to query closure info by closure_id
  def get_closure_info(self, closure_id) -> Optional[ClosureInfo]:
    connection = self.get_connection()
    if not connection:
      return None

    closure_info = None
    try:
      cursor = connection.cursor()
      query = """
      SELECT c.closure_id, c.status, c.start_date, c.last_date, c.reason,
        STRING_AGG(r.room_id, '' ORDER BY r.ctid) AS room_ids, c.created, c.modified
      FROM Closures c
      JOIN RoomClosures rc ON c.closure_id = rc.closure_id
      JOIN Rooms r ON rc.room_id = r.room_id
      WHERE c.closure_id = %s
        AND c.status = 'valid'::closure_statuses
      GROUP BY c.closure_id;
      """
      cursor.execute(query, (closure_id,))
      row = cursor.fetchone()
      cursor.close()

      if (row):
        closure_info = ClosureInfo(
          closure_id==row[0],
          status=row[1],
          start_date=row[2],
          last_date=row[3],
          reason=row[4] or '',
          room_ids=row[5],
          created=row[6],
          modified=row[7]
        )
    except Exception as e:
      self.logger.error(f"Error querying closure info: {e}")
    finally:
      self.release_connection(connection)
    return closure_info

  def insert_closure(self, closure_info: ClosureInfo) -> Optional[int]:
    connection = self.get_connection()
    if not connection:
      return None

    closure_id = None
    try:
      cursor = connection.cursor()

      # Insert into Closures table
      insert_query = """
      INSERT INTO Closures (status, start_date, last_date, reason)
      VALUES (%s, %s, %s, %s)
      RETURNING closure_id;
      """
      cursor.execute(insert_query, (
        closure_info.status,
        closure_info.start_date,
        closure_info.last_date,
        closure_info.reason
      ))
      closure_id = cursor.fetchone()[0]

      # Insert room-closure relationships into RoomClosures table
      for room_id in closure_info.room_ids:
        insert_room_closures_query = """
        INSERT INTO RoomClosures (closure_id, room_id)
        VALUES (%s, %s);
        """
        cursor.execute(insert_room_closures_query, (closure_id, room_id))

      cursor.close()

    except Exception as e:
      self.logger.error(f"Error inserting closure: {e}")
    finally:
      self.release_connection(connection)

    return closure_id

  def delete_closure(self, closure_id: int) -> bool:
    connection = self.get_connection()
    if not connection:
      return False

    try:
      cursor = connection.cursor()

      # Delete the closure
      delete_closure_query = """
      UPDATE Closures
      SET status = 'deleted'::closure_statuses
      WHERE closure_id = %s
      """
      cursor.execute(delete_closure_query, (closure_id,))
      cursor.close()

    except Exception as e:
      self.logger.error(f"Error deleting closure {closure_id}: {e}")
      return False
    finally:
      self.release_connection(connection)
    return True

  def search_closure_by_date(self, date) -> Optional[list[ClosureInfo]]:
    connection = self.get_connection()
    if not connection:
      return None

    matches = []
    try:
      cursor = connection.cursor()

      # SQL query to find closures containing the target date
      query = """
      SELECT c.closure_id, c.status, c.start_date, c.last_date, c.reason,
        STRING_AGG(r.room_id, '' ORDER BY r.ctid) AS room_ids, c.created, c.modified
      FROM Closures c
      JOIN RoomClosures rc ON c.closure_id = rc.closure_id
      JOIN Rooms r ON rc.room_id = r.room_id
      WHERE %s BETWEEN c.start_date AND c.last_date
        AND c.status = 'valid'::closure_statuses
      GROUP BY c.closure_id;
      """

      cursor.execute(query, (date,))
      rows = cursor.fetchall()
      cursor.close()

      for row in rows:
        closure_info = ClosureInfo(
          closure_id=row[0],
          status=row[1],
          start_date=row[2],
          last_date=row[3],
          reason=row[4] or '',
          room_ids=row[5],
          created=row[6],
          modified=row[7]
        )
        matches.append(closure_info)

    except Exception as e:
      self.logger.error(f"Error searching bookings by check-in date: {e}")
      matches = None

    finally:
      self.release_connection(connection)

    return matches

  def get_latest_closures(self, last_sync_time) -> Optional[list[ClosureInfo]]:
    connection = self.get_connection()
    if not connection:
      return None

    matches = []
    try:
      cursor = connection.cursor()

      # SQL query to get bookings created or modified after the last sync time
      query = """
      SELECT c.closure_id, c.status, c.start_date, c.last_date, c.reason,
        STRING_AGG(r.room_id, '' ORDER BY r.ctid) AS room_ids, c.created, c.modified
      FROM Closures c
      JOIN RoomClosures rc ON c.closure_id = rc.closure_id
      JOIN Rooms r ON rc.room_id = r.room_id
      WHERE c.created >= %s OR c.modified >= %s
      GROUP BY c.closure_id
      ORDER BY c.created;
      """

      cursor.execute(query, (last_sync_time, last_sync_time))
      rows = cursor.fetchall()
      cursor.close()

      for row in rows:
        closure_info = ClosureInfo(
          closure_id=row[0],
          status=row[1],
          start_date=row[2],
          last_date=row[3],
          reason=row[4] or '',
          room_ids=row[5],
          created=row[6],
          modified=row[7]
        )
        matches.append(closure_info)

    except Exception as e:
      self.logger.error(f"Error fetching latest bookings: {e}")
      matches = None

    finally:
      self.release_connection(connection)

    return matches

  ##########################################
  ###   Customer data access functions   ###
  ##########################################

  def upsert_customer(self, customer: Customer)-> Optional[int]:
    connection = self.get_connection()
    if not connection:
      return None

    customer_id = None
    try:
      cursor = connection.cursor()
      existing_customer = None
      if not is_generic_phone_number(customer.phone_number):
        # Check if the customer exists based on phone number
        cursor.execute("SELECT customer_id, name, phone_number FROM Customers WHERE phone_number=%s", (customer.phone_number,))
        existing_customer = cursor.fetchone()
      elif not is_generic_name(customer.name):
        # Check if the customer exists based on non-generic name
        cursor.execute("SELECT customer_id, name, phone_number FROM Customers WHERE name=%s", (customer.name,))
        existing_customer = cursor.fetchone()

      if existing_customer:
        customer_id, existing_name, existing_phone_number = existing_customer
        # Compare names and phone numbers and update if necessary
        if not is_generic_name(customer.name) and customer.name != existing_name:
          self.logger.info(f"Updating customer name from {existing_name} to {customer.name}")
          cursor.execute("UPDATE Customers SET name=%s WHERE customer_id=%s", (customer.name, customer_id))
        if not is_generic_phone_number(customer.phone_number) and customer.phone_number != existing_phone_number:
          self.logger.info(f"Updating customer phone number from {existing_phone_number} to {customer.phone_number}")
          cursor.execute("UPDATE Customers SET phone_number=%s WHERE customer_id=%s", (customer.phone_number, customer_id))
      else:
        # Insert a new customer record
        cursor.execute("""
        INSERT INTO Customers (name, phone_number)
        VALUES (%s, %s)
        RETURNING customer_id;
        """, (customer.name, customer.phone_number))
        customer_id = cursor.fetchone()[0]
      cursor.close()
    except Exception as e:
      self.logger.error(f"Error query customer: {e}")
    finally:
      self.release_connection(connection)
    return customer_id

  def get_customer_by_phone_number(self, phone_number) -> Optional[Customer]:
    connection = self.get_connection()
    if not connection:
      return None

    customer = None
    try:
      cursor = connection.cursor()
      cursor.execute("SELECT customer_id, name, phone_number, created, modified FROM Customers WHERE phone_number=%s", (phone_number,))
      row = cursor.fetchone()
      cursor.close()
      if (row):
        customer = Customer(
          customer_id=row[0],
          name=row[1],
          phone_number=row[2],
          created=row[3],
          modified=row[4]
        )
    except Exception as e:
      self.logger.error(f"Error query customer: {e}")
    finally:
      self.release_connection(connection)

    return customer

  ##########################################
  ###     Room data access functions     ###
  ##########################################

  def get_all_room_ids(self) -> Optional[list[str]]:
    connection = self.get_connection()
    if not connection:
      return None

    available_room_ids = None
    try:
      cursor = connection.cursor()

      query = "SELECT room_id FROM Rooms ORDER BY ctid;"
      cursor.execute(query)
      available_room_ids = [row[0] for row in cursor.fetchall()]
      cursor.close()
    except Exception as e:
      self.logger.error(f"Error retrieving all room ids: {e}")
    finally:
      self.release_connection(connection)
    return available_room_ids

  ##########################################
  ### RoomBooking data access functions  ###
  ##########################################

  def get_available_room_ids(self, check_in_date, last_date):
    connection = self.get_connection()
    if not connection:
        return None

    available_room_ids = None
    try:
      cursor = connection.cursor()

      query = """
      SELECT r.room_id
      FROM Rooms r
      WHERE r.room_status = 'available'::room_statuses -- Ensure room is not permanently closed
        AND r.room_id NOT IN (
          SELECT rb.room_id
          FROM RoomBookings rb
          JOIN Bookings b ON rb.booking_id = b.booking_id
          WHERE b.status != 'canceled'::booking_statuses -- Ignore canceled bookings
            AND (b.check_in_date <= %s AND b.last_date >= %s)
        )
      ORDER BY r.ctid;
      """

      # Execute query with date range parameters
      cursor.execute(query, (last_date, check_in_date))
      available_room_ids = [row[0] for row in cursor.fetchall()]
      cursor.close()
    except Exception as e:
      self.logger.error(f"Error fetching available room ids: {e}")
    finally:
      self.release_connection(connection)
    return available_room_ids

  def get_total_price_estimation(self, room_ids, check_in_date, last_date):
    connection = self.get_connection()
    if not connection:
        return None

    total_price = None
    try:
      cursor = connection.cursor()

      # Fetch pricing details for the specified rooms
      query = """
      SELECT room_id, holiday_price_per_night, weekday_price_per_night
      FROM Rooms
      WHERE room_id IN %s
      """
      cursor.execute(query, (tuple(room_ids),))
      rooms = cursor.fetchall()

      # Map room pricing for quick lookup
      room_pricing = {
          room_id: {
              "holiday_price": holiday_price,
              "weekday_price": weekday_price
          }
          for room_id, holiday_price, weekday_price in rooms
      }

      # Calculate total price
      total_price = 0
      current_date = check_in_date

      while current_date <= last_date:
        # Determine if the current date is a holiday (Saturday)
        is_holiday = current_date.weekday() == 5  # 5 = Saturday

        # Add price for each room for the current date
        for room_id in room_ids:
          if is_holiday:
            total_price += int(room_pricing[room_id]["holiday_price"])
          else:
            total_price += int(room_pricing[room_id]["weekday_price"])

        # Move to the next day
        current_date += timedelta(days=1)

    except Exception as e:
      self.logger.error(f"Error calculating total price: {e}")
    finally:
      self.release_connection(connection)
    return total_price

  ##########################################
  ###  SyncRecord data access functions  ###
  ##########################################

  def get_latest_sync_time(self, sync_type="sql_to_google_calendar") -> Optional[datetime]:
    connection = self.get_connection()
    if not connection:
      return None

    latest_sync_time = None
    try:
      cursor = connection.cursor()

      # Query to get the latest successful sync time for the specified sync type
      query = """
      SELECT synced_time
      FROM SyncRecords
      WHERE sync_type = %s AND success = TRUE
      ORDER BY synced_time DESC
      LIMIT 1;
      """

      cursor.execute(query, (sync_type,))
      result = cursor.fetchone()
      if result:
        latest_sync_time = result[0]  # Get the timestamp from the query result
      cursor.close()
    except Exception as e:
      self.logger.error(f"Error retrieving latest sync time for {sync_type}: {e}")
    finally:
      self.release_connection(connection)
    return latest_sync_time or datetime.min  # Return minimum datetime if no successful sync found

  def log_sync_record(self, sync_type, synced_booking_ids, success, error_message=None) -> Optional[int]:
    connection = self.get_connection()
    if not connection:
      return None

    sync_id = None
    try:
      cursor = connection.cursor()

      # Insert sync record into SyncRecords table
      query = """
      INSERT INTO SyncRecords (sync_type, synced_booking_ids, success, error_message)
      VALUES (%s, %s, %s, %s)
      RETURNING sync_id
      """

      cursor.execute(query, (sync_type, ' , '.join([str(booking_id) for booking_id in synced_booking_ids]), success, error_message))
      sync_id = cursor.fetchone()[0]
      cursor.close()
    except Exception as e:
      self.logger.error(f"Error logging sync record: {e}")
    finally:
      self.release_connection(connection)
    return sync_id
