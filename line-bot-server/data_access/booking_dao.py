import psycopg2
import psycopg2.pool
from data_access.data_class.booking_info import BookingInfo

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
        self.logger.info("Successfully retrieved connection from the pool")
      return connection
    except Exception as e:
      self.logger.error(f"Error retrieving connection from pool: {e}")
      return None

  def release_connection(self, connection):
    try:
      if connection:
        self.connection_pool.putconn(connection)
        self.logger.info("Connection returned to the pool")
    except Exception as e:
      self.logger.error(f"Error releasing connection back to the pool: {e}")

  def close_all_connections(self):
    try:
      self.connection_pool.closeall()
      self.logger.info("All connections in the pool closed")
    except Exception as e:
      self.logger.error(f"Error closing all connections in the pool: {e}")

  # Function to query the booking info by booking_id
  def get_booking_info(self, booking_id):
    connection = self.get_connection()
    if not connection:
      return None
    try:
      cursor = connection.cursor()
      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date,
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_status,
        STRING_AGG(r.room_id, '') AS room_ids
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
        prepayment_status=row[10],
        room_ids=row[11]
      )
      return booking_info
    except Exception as e:
      self.logger.error(f"Error querying booking info: {e}")
      return None
    finally:
      self.release_connection(connection)

  def search_booking_by_keyword(self, keyword, limit=3):
    connection = self.get_connection()
    if not connection:
      return None

    try:
      cursor = connection.cursor()

      # SQL query to search for bookings by booking_id, phone_number, or customer_name
      query = """
      SELECT b.booking_id, b.status, c.name, c.phone_number, b.check_in_date, b.last_date, 
        b.total_price, b.notes, b.source, b.prepayment, b.prepayment_status,
        STRING_AGG(r.room_id, '') AS room_ids
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
          prepayment_status=row[10],
          room_ids=row[11]
        )
        matches.append(booking_info)

      return matches

    except Exception as e:
        self.logger.error(f"Error searching bookings: {e}")
        return None

    finally:
        self.release_connection(connection)
