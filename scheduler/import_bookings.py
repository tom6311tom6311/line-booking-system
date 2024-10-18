import os
import re
import psycopg2

GENERIC_NAMES = ['先生', '小姐', '無名氏']
VALID_BOOKING_SOURCES = ['自洽', 'Booking_com', 'FB', 'Agoda', '台灣旅宿', 'Airbnb']
INVALID_PHONE_NUMBER_POSTFIX = '000000'

# Connection details (replace with your actual values)
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

# Example booking text block
SORTED_BOOKINGS_FILE_PATH = './data/sorted_bookings.txt'

# Function to parse the booking text block
def parse_booking(text):
  try:
    booking_data = {}

    # Check if the booking is canceled
    if '[取消]' in text:
      booking_data['status'] = 'canceled'
    else:
      booking_data['status'] = 'new'  # Default to 'new' unless specified otherwise

    # Using regular expressions to extract key fields
    booking_data['booking_id'] = int(re.search(r'ＩＤ：(\d+)', text).group(1))
    booking_data['customer_name'] = re.search(r'姓名：(.+)', text).group(1)

    # Extract phone_number (starts with + and followed by digits or may start with 0 for Taiwan format)
    phone_match = re.search(r'電話：(\+?\d+)', text)
    if phone_match:
        phone_number = phone_match.group(1)
        # Convert phone numbers starting with '0' to '+886' if necessary
        if phone_number.startswith('0'):
            booking_data['phone_number'] = '+886' + phone_number[1:]
        else:
            booking_data['phone_number'] = phone_number

    booking_data['room_name_string'] = re.search(r'預計讓他睡：(.+)', text).group(1)  # This will be processed later to extract rooms
    booking_data['check_in_date'] = re.search(r'入住日期：(\d{4}/\d{2}/\d{2})', text).group(1)
    booking_data['check_out_date'] = re.search(r'退房日期：(\d{4}/\d{2}/\d{2})', text).group(1)
    booking_data['total_price'] = float(re.search(r'總金額：(\d+)', text).group(1))
    booking_data['source'] = re.search(r'來源：(.+)', text).group(1).replace('_', '.')

    if (booking_data['source'] == 'Booking.com'):
      booking_data['source'] = 'Booking_com'

    # Parse the prepayment and status from the "訂金" line
    prepayment_info = re.search(r'訂金：(\d+)元/(.+)', text)
    booking_data['prepayment'] = float(prepayment_info.group(1))
    prepayment_status = prepayment_info.group(2)
    if prepayment_status == '已付':
      booking_data['status'] = 'prepaid'  # If paid, mark as 'prepaid'

    booking_data['notes'] = re.search(r'備註：(.*)', text).group(1)

    return booking_data
  except Exception as e:
    print(f"Error parsing text: {text}\n Error: {e}")
    return None

# Function to do sanity check on the booking field values. Print error if any invalid field found
def validate_booking(booking_data):
  if (booking_data['booking_id'] <= 0):
    print(f"[Validation Error] Invalid booking_id: {booking_data['booking_id']}")
  if (len(booking_data['customer_name']) <= 0):
    print(f"[Validation Error] #{booking_data['booking_id']} with no customer name")
  if (len(booking_data['phone_number']) <= 0):
    print(f"[Validation Error] #{booking_data['booking_id']} with no phone number")
  if (len(booking_data['room_name_string']) <= 0):
    print(f"[Validation Error] #{booking_data['booking_id']} with no room specified")
  if (len(booking_data['check_in_date']) <= 0):
    print(f"[Validation Error] #{booking_data['booking_id']} with no check_in_date")
  if (len(booking_data['check_out_date']) <= 0):
    print(f"[Validation Error] #{booking_data['booking_id']} with no check_out_date")
  if (booking_data['total_price'] <= 0):
    print(f"[Validation Error] #{booking_data['booking_id']} with total_price <= 0")
  if (booking_data['source'] not in VALID_BOOKING_SOURCES):
    print(f"[Validation Error] #{booking_data['booking_id']} with invalid source: {booking_data['source']}")

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
  for g_name in GENERIC_NAMES:
    if g_name in name:
      return True
  return False

# Function to insert or update customer data into PostgreSQL
def insert_or_update_customer(cursor, booking_data):
  existing_customer = False
  if booking_data['phone_number'] and not booking_data['phone_number'].endswith(INVALID_PHONE_NUMBER_POSTFIX):
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

# with open(SORTED_BOOKINGS_FILE_PATH, 'r', encoding='utf-8') as f:
#   content = f.read()
#   booking_text_list = content.split("\n\n")
#   for booking_text in booking_text_list:
#     booking_data = parse_booking(booking_text)
#     if (not booking_data):
#       continue
#     validate_booking(booking_data)
#     insert_booking(booking_data)
