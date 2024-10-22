import re
from datetime import datetime

def is_valid_date(date_str):
  try:
    datetime.strptime(date_str, '%Y-%m-%d')
    return True
  except ValueError:
    return False

def extract_date_from_string_template(template, input_str):
  # Define a pattern to match the date in yyyy/mm/dd format
  pattern = re.sub(r'{date}', r'(\d{4})(/|-)(\d{2})(/|-)(\d{2})', template)

  # Search for the date pattern in the input string
  match = re.search(pattern, input_str)

  if match:
    # Extract the matched groups and reformat into yyyy-mm-dd
    year, month, day = match.groups()
    parsed_date = f"{year}-{month}-{day}"
    return parsed_date
  else:
    return None
