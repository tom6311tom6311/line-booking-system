import os
import logging
import subprocess
from datetime import datetime
from const import db_config

BACKUP_DIR = './backup/mysql_backups'
MAX_BACKUPS = 15

def backup_mysql():
  """
  Perform a MySQL backup and manage file rotation.
  """
  try:
    # Create the backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"{db_config.DB_NAME}-{timestamp}.sql")

    # Perform the database backup using mysqldump
    command = [
      "mysqldump",
      "-h", db_config.DB_HOST,
      "-u", db_config.DB_USER,
      f"-p{db_config.DB_PASSWORD}",
      db_config.DB_NAME,
    ]
    with open(backup_file, "w") as f:
      subprocess.run(command, stdout=f, check=True)
    logging.info(f"Backup successful: {backup_file}")

    # Handle file rotation
    rotate_backups()

  except subprocess.CalledProcessError as e:
    logging.error(f"Backup failed: {e}")
  except Exception as e:
    logging.error(f"Unexpected error during backup: {e}")

def rotate_backups():
  """
  Delete the oldest backup files if the total number exceeds MAX_BACKUPS.
  """
  try:
    # List backup files sorted by creation time
    backups = sorted(
      [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR)],
      key=os.path.getctime,
    )

    # Remove oldest files if exceeding MAX_BACKUPS
    while len(backups) > MAX_BACKUPS:
      oldest = backups.pop(0)
      os.remove(oldest)
      logging.info(f"Deleted oldest backup: {oldest}")

  except Exception as e:
    logging.error(f"Error during file rotation: {e}")
