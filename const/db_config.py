import os

# DB Connection
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_CONNECT_TIMEOUT = os.getenv('DB_CONNECT_TIMEOUT', '5')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_SSLMODE = os.getenv('DB_SSLMODE')
DB_SSLROOTCERT = os.getenv('DB_SSLROOTCERT')
