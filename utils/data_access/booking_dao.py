import psycopg2
import psycopg2.pool
from typing import Optional
from datetime import datetime, timedelta
from const.booking_const import INVALID_PHONE_NUMBER_POSTFIX
from utils.booking_utils import is_generic_name
from .data_class.booking_info import BookingInfo
from .data_class.customer import Customer


class BookingDAO:
  _instance = None

  def __init__(self, db_config, logger):
    self.db_config = db_config
    self.logger = logger
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
  def get_instance(cls, db_config=None, logger=None):
    if cls._instance is None:
      cls._instance = BookingDAO(db_config, logger)
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
        STRING_AGG(r.room_id, '') AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE b.booking_id = %s
      GROUP BY b.booking_id, c.name, c.phone_number;
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
          total_price=row[6],
          notes=row[7],
          source=row[8],
          prepayment=row[9],
          prepayment_note=row[10],
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
    # upsert customer first
    customer_id = self.upsert_customer(Customer(
      name=booking_info.customer_name,
      phone_number=booking_info.phone_number
    ))
    existing_booking_info = self.get_booking_info(booking_info.booking_id)

    connection = self.get_connection()
    if not connection:
      return None

    booking_id = None
    try:
      cursor = connection.cursor()
      if existing_booking_info:
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
    except Exception as e:
      self.logger.error(f"Error upsert booking {booking_id}: {e}")
    finally:
      self.release_connection(connection)
    return booking_id

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
        STRING_AGG(r.room_id, '') AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE b.booking_id::text LIKE %s
        OR c.phone_number LIKE %s
        OR c.name LIKE %s
      GROUP BY b.booking_id, c.name, c.phone_number
      ORDER BY b.booking_id DESC
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
          total_price=row[6],
          notes=row[7],
          source=row[8],
          prepayment=row[9],
          prepayment_note=row[10],
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

  def search_booking_by_date(self, date, is_check_in = True) -> Optional[list[BookingInfo]]:
    connection = self.get_connection()
    if not connection:
      return None

    try:
      date_field = 'check_in_date' if is_check_in else 'last_date'
      cursor = connection.cursor()

      # SQL query to search for bookings by check-in date
      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date,
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_note, b.prepayment_status,
        STRING_AGG(r.room_id, '') AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE b.{date_field} = %s
      GROUP BY b.booking_id, c.name, c.phone_number
      ORDER BY b.booking_id;
      """

      cursor.execute(query.format(date_field=date_field), (date,))
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
          total_price=row[6],
          notes=row[7],
          source=row[8],
          prepayment=row[9],
          prepayment_note=row[10],
          prepayment_status=row[11],
          room_ids=row[12],
          created=row[13],
          modified=row[14]
        )
        matches.append(booking_info)

      return matches

    except Exception as e:
      self.logger.error(f"Error searching bookings by check-in date: {e}")
      return None

    finally:
      self.release_connection(connection)

  def get_latest_bookings(self, last_sync_time) -> Optional[list[BookingInfo]]:
    connection = self.get_connection()
    if not connection:
      return None

    try:
      cursor = connection.cursor()

      # SQL query to get bookings created or modified after the last sync time
      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date,
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_note, b.prepayment_status,
        STRING_AGG(r.room_id, '') AS room_ids, b.created, b.modified
      FROM Bookings b
      JOIN Customers c ON b.customer_id = c.customer_id
      JOIN RoomBookings rb ON b.booking_id = rb.booking_id
      JOIN Rooms r ON rb.room_id = r.room_id
      WHERE b.created >= %s OR b.modified >= %s
      GROUP BY b.booking_id, c.name, c.phone_number
      ORDER BY b.created DESC
      LIMIT 1;
      """

      cursor.execute(query, (last_sync_time, last_sync_time))
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
          total_price=row[6],
          notes=row[7],
          source=row[8],
          prepayment=row[9],
          prepayment_note=row[10],
          prepayment_status=row[11],
          room_ids=row[12],
          created=row[13],
          modified=row[14]
        )
        matches.append(booking_info)

      return matches

    except Exception as e:
      self.logger.error(f"Error fetching latest bookings: {e}")
      return None

    finally:
      self.release_connection(connection)

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
      if not customer.phone_number.endswith(INVALID_PHONE_NUMBER_POSTFIX):
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
        if is_generic_name(existing_name) and not is_generic_name(customer.name):
          self.logger.info(f"Updating customer name from {existing_name} to {customer.name}")
          cursor.execute("UPDATE Customers SET name=%s WHERE customer_id=%s", (customer.name, customer_id))
        if existing_phone_number.endswith(INVALID_PHONE_NUMBER_POSTFIX) and not customer.phone_number.endswith(INVALID_PHONE_NUMBER_POSTFIX):
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

      query = "SELECT room_id FROM Rooms;"
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
      WHERE r.room_status = 'available' -- Ensure room is not permanently closed
        AND r.room_id NOT IN (
          SELECT rb.room_id
          FROM RoomBookings rb
          JOIN Bookings b ON rb.booking_id = b.booking_id
          WHERE b.status != 'canceled' -- Ignore canceled bookings
            AND (b.check_in_date <= %s AND b.last_date >= %s)
        )
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
            total_price += room_pricing[room_id]["holiday_price"]
          else:
            total_price += room_pricing[room_id]["weekday_price"]

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