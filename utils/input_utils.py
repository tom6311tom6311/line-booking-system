import re
from datetime import datetime

def is_valid_date(date_str):
  try:
    datetime.strptime(date_str, '%Y-%m-%d')
    return True
  except ValueError:
    return False

def is_valid_phone_number(phone_number: str):
  # Check if the phone number starts with '+' or '0' and contains no spaces
  if not phone_number.startswith(('+', '0')) or ' ' in phone_number:
    return False

  # If the phone number starts with '+', ensure it contains only digits after '+'
  if phone_number.startswith('+'):
    if not re.fullmatch(r'\+\d+', phone_number):
      return False

  # If the phone number starts with '09', ensure length is exactly 10
  elif phone_number.startswith('09'):
    if len(phone_number) != 10:
      return False

  # If the phone number starts with '0' (but not '09'), ensure it contains only digits
  elif phone_number.startswith('0'):
    if not phone_number.isdigit():
      return False

  return True

# Convert phone numbers starting with '0' to '+886' if necessary
def format_phone_number(phone_number: str):
  if phone_number.startswith('0'):
    return '+886' + phone_number[1:]
  return phone_number

def is_valid_num_nights(num_nights: str):
  if num_nights.isdigit():
    # Convert to integer and check range
    num_nights = int(num_nights)
    if 1 <= num_nights <= 15:
      return True
  return False

def is_valid_price(price: str):
  if price.isdigit():
    # Convert to integer and check range
    price = int(price)
    if 0 <= price <= 100000:
      return True
  return False

def extract_booking_id(command, template):
  """
  Checks if the input string matches the given template and extracts the booking_id if it matches.

  Args:
      command (str): The input string to validate and extract from.
      template (str): The template string containing '{booking_id}' placeholder.

  Returns:
      int: The extracted booking_id if valid, None otherwise.
  """
  # Replace the {booking_id} placeholder with a regex pattern to capture positive integers
  pattern = re.escape(template).replace(r'\{booking_id\}', r'(\d+)')

  # Match the input string against the dynamically created pattern
  match = re.fullmatch(pattern, command)

  if match:
    # Extract booking_id and ensure it is a positive integer
    booking_id = int(match.group(1))
    if booking_id > 0:
      return booking_id

  return None
