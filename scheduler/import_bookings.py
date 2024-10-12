import os
import re
import psycopg2

# Connection details (replace with your actual values)
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Example booking text block
booking_text = """
[訂單][取消]
ＩＤ：2
姓名：翁先生
電話：0929224967
房型/間數：雙人房/1間
入住日期：2016/09/03
退房日期：2016/09/04
晚數：1
總金額：2000
備註：
來源：Booking_com
訂金：0元/已付
預計讓他睡：紅莓
"""

# Function to parse the booking text block
def parse_booking(text):
  booking_data = {}

  # Check if the booking is canceled
  if '[取消]' in text:
    booking_data['status'] = 'canceled'
  else:
    booking_data['status'] = 'new'  # Default to 'new' unless specified otherwise

  # Using regular expressions to extract key fields
  booking_data['booking_id'] = int(re.search(r'ＩＤ：(\d+)', text).group(1))
  booking_data['customer_name'] = re.search(r'姓名：(.+)', text).group(1)

  # Convert phone numbers starting with '0' to '+886'
  phone_number = re.search(r'電話：(\d+)', text).group(1)
  if phone_number.startswith('0'):
    booking_data['phone_number'] = '+886' + phone_number[1:]
  else:
    booking_data['phone_number'] = phone_number

  booking_data['room_name_string'] = re.search(r'預計讓他睡：(.+)', text).group(1)  # This will be processed later to extract rooms
  booking_data['check_in_date'] = re.search(r'入住日期：(\d{4}/\d{2}/\d{2})', text).group(1)
  booking_data['check_out_date'] = re.search(r'退房日期：(\d{4}/\d{2}/\d{2})', text).group(1)
  booking_data['total_price'] = float(re.search(r'總金額：(\d+)', text).group(1))
  booking_data['source'] = re.search(r'來源：(.+)', text).group(1).replace('_', '.')

  # Parse the prepayment and status from the "訂金" line
  prepayment_info = re.search(r'訂金：(\d+)元/(.+)', text)
  booking_data['prepayment'] = float(prepayment_info.group(1))
  prepayment_status = prepayment_info.group(2)
  if prepayment_status == '已付':
    booking_data['status'] = 'prepaid'  # If paid, mark as 'prepaid'

  booking_data['notes'] = re.search(r'備註：(.*)', text).group(1)

  return booking_data

# Function to extract associated room_ids from room_name_string
def extract_room_ids(cursor, room_name_string):
  room_ids = []
  # Query to get all available room short_names
  cursor.execute("SELECT room_id FROM Rooms")
  available_room_ids = [row[0] for row in cursor.fetchall()]

  # Match each character in room_name_string to an available room_id
  for char in room_name_string:
    if char in available_room_ids:
      room_ids.append(char)

  return room_ids

# Function to determine if a customer name is generic
def is_generic_name(name):
  generic_names = ['先生', '小姐', '無名氏']
  for g_name in generic_names:
    if g_name in name:
      return True
  return False

# Function to insert or update customer data into PostgreSQL
def insert_or_update_customer(cursor, booking_data):
  existing_customer = False
  if booking_data['phone_number'] and not booking_data['phone_number'].endswith('000000'):
    # Check if the customer exists based on phone number
    cursor.execute("SELECT customer_id, name FROM Customers WHERE phone_number=%s", (booking_data['phone_number'],))
    existing_customer = cursor.fetchone()

  if existing_customer:
    customer_id, existing_name = existing_customer
    # Compare names and update if necessary
    if is_generic_name(existing_name) and not is_generic_name(booking_data['customer_name']):
      print(f"Updating customer name from {existing_name} to {booking_data['customer_name']}")
      cursor.execute("UPDATE Customers SET name=%s WHERE customer_id=%s", (booking_data['customer_name'], customer_id))
  else:
    # Insert a new customer record
    cursor.execute("""
    INSERT INTO Customers (name, phone_number)
    VALUES (%s, %s)
    RETURNING customer_id;
    """, (booking_data['customer_name'], booking_data['phone_number']))
    customer_id = cursor.fetchone()[0]

  return customer_id

# Function to insert booking data into PostgreSQL
def insert_booking(booking_data):
  try:
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
      host=DB_HOST,
      dbname=DB_NAME,
      user=DB_USER,
      password=DB_PASSWORD
    )
    cursor = conn.cursor()

    # Insert or update customer data
    customer_id = insert_or_update_customer(cursor, booking_data)

    # Insert booking data
    insert_booking_query = """
    INSERT INTO Bookings (customer_id, check_in_date, last_date, total_price, prepayment, source, status, notes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING booking_id;
    """
    cursor.execute(insert_booking_query, (
      customer_id,
      booking_data['check_in_date'],
      booking_data['check_out_date'],
      booking_data['total_price'],
      booking_data['prepayment'],
      booking_data['source'],
      booking_data['status'],  # Status: new, prepaid, or canceled
      booking_data['notes']
    ))

    # Get the booking ID
    booking_id = cursor.fetchone()[0]

    # Extract associated room_ids from room_name_string
    room_ids = extract_room_ids(cursor, booking_data['room_name_string'])

    # Insert room-booking relationships into RoomBookings table
    for room_id in room_ids:
      insert_room_booking_query = """
      INSERT INTO RoomBookings (booking_id, room_id)
      VALUES (%s, %s);
      """
      cursor.execute(insert_room_booking_query, (
        booking_id,
        room_id
      ))

    # Commit the transaction
    conn.commit()
    print(f"Booking #{booking_id} imported successfully with rooms: {room_ids}")

  except Exception as e:
    print(f"Error: {e}")
  finally:
    if conn:
      cursor.close()
      conn.close()

# Parse the text block and insert the booking into the database
booking_data = parse_booking(booking_text)
insert_booking(booking_data)
