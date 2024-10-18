import re

# Example file path (replace with the path to your file)
file_path = 'historical_bookings.txt'
sorted_file_path = 'sorted_bookings.txt'

# Function to parse a single booking text block and extract booking_id
def parse_booking(text):
  match = re.search(r'ＩＤ：(\d+)', text)
  if match:
    booking_id = int(match.group(1))
    if len(text.split("\n")) > 13:
      print(f"Warning: wrong booking format detected: {booking_id}")
    return booking_id
  print(f"Warning: cannot parse booking text: {text}")
  return None

# Function to load bookings from file
def load_bookings(file_path):
  with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    # Assuming each booking is separated by an empty line
    bookings = content.split("\n\n")
  return bookings

# Function to check for conflicts and sort by booking_id
def process_bookings(bookings):
  booking_dict = {}
  conflicts = []
  
  for booking in bookings:
    booking_id = parse_booking(booking)
    if booking_id is not None:
      if booking_id in booking_dict:
        conflicts.append(booking_id)  # Duplicate found
      else:
        booking_dict[booking_id] = booking

  for booking_id in range(1, len(booking_dict)):
    if booking_id not in booking_dict:
      print(f"Missing booking ID found: {booking_id}")
  
  # Sort bookings by booking_id
  sorted_bookings = sorted(booking_dict.items())
  
  return sorted_bookings, conflicts

# Function to write sorted bookings to a new file
def write_sorted_bookings(sorted_bookings, sorted_file_path):
  with open(sorted_file_path, 'w', encoding='utf-8') as f:
    for _, booking in sorted_bookings:
      f.write(booking.strip() + "\n\n")

# Load the historical bookings
bookings = load_bookings(file_path)

# Process and sort the bookings, checking for conflicts
sorted_bookings, conflicts = process_bookings(bookings)

# Output conflicts if any
if conflicts:
  print(f"Conflicted booking IDs found: {conflicts}")
else:
  print("No conflicts found.")

# Write the sorted bookings to a new file
write_sorted_bookings(sorted_bookings, sorted_file_path)

print(f"Sorted bookings have been written to {sorted_file_path}")
