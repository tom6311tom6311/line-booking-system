import os
import logging
import subprocess
from datetime import datetime
from const import db_config

BACKUP_DIR = './backup/sql_backups'
MAX_BACKUPS = 15

def backup_sql():
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
      "pg_dump",
      "-h", db_config.DB_HOST,
      "-U", db_config.DB_USER,
      "-F", "c",  # Custom format for compressed backup
      "-f", backup_file,
      db_config.DB_NAME,
    ]

    # Set the password environment variable for pg_dump
    env = os.environ.copy()
    env["PGPASSWORD"] = db_config.DB_PASSWORD

    with open(backup_file, "w") as f:
      subprocess.run(command, env=env, check=True)
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
