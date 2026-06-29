# Line Booking System

This project is a microservices-based **Room Booking Management System** built with Docker Compose. It includes a **Python-Flask LINE bot server**, scheduler jobs, and an external PostgreSQL database such as AWS RDS.

## Features

- **Microservices Architecture**: Services are containerized using Docker.
- **External PostgreSQL Database**: Stores booking data and related information.
- **LINE Bot Integration**: Admins and stakeholders interact with the system via a LINE bot.
- **Synchronization**: Bookings are synchronized with Google Calendar and Notion.

## Project Structure

```
/project-root
│
├── /db/sql                # PostgreSQL schema/reference SQL
├── /line-bot-server        # Python-Flask LINE bot service
├── /scheduler              # Scheduled sync/notification jobs
└── docker-compose.yml      # Docker Compose configuration
```

## Prerequisites

- **Docker**: Ensure Docker is installed on your machine.
- **LINE Developer Account**: You need a LINE Developer account with a bot set up. You'll need the **Channel Access Token** and **Channel Secret** for the bot.

## Getting Started

1. Clone the repository:
   ```bash
   git clone git@github.com:tom6311tom6311/line-booking-system.git
   cd line-booking-system
   ```

2. Set up environment variables: (after copy please adjust the values in .env to your settings)
   ```bash
   cp .env.template .env
   ```

3. Build and run the project:
   ```bash
   docker-compose up --build
   ```

## Database Configuration

The app reads PostgreSQL connection settings from environment variables:

```bash
DB_HOST=YOUR_RDS_ENDPOINT
DB_PORT=5432
DB_USER=YOUR_DB_USER
DB_PASSWORD=YOUR_DB_PASSWORD
DB_NAME=YOUR_DB_NAME
DB_SSLMODE=
DB_SSLROOTCERT=
```

Set `DB_HOST` to the RDS endpoint, keep `DB_PORT=5432`, and set `DB_SSLMODE=verify-full` if you want certificate hostname verification. Download the AWS RDS CA bundle as `certs/global-bundle.pem` and set `DB_SSLROOTCERT=/app/certs/global-bundle.pem`.

If Google Calendar sync is enabled, place the service account file at `secrets/google_service_account.json` and set `GOOGLE_SERVICE_ACCOUNT_CRED_FILE=/app/secrets/google_service_account.json`.

```bash
docker-compose --env-file .env.prod up -d --build
```

On Lightsail, point your domain DNS to the instance static IP, open ports 80 and 443, and let the bundled Caddy service provision HTTPS automatically. Configure the LINE webhook URL as `https://your-domain.com/callback`.

## How It Works

- **LINE Bot Server**: Admins can interact with the system via the LINE bot, handling booking creation, updates, and more.
- **PostgreSQL**: An external database stores all booking-related data, including customer info, rooms, and booking status.
- **Scheduler (Future Implementation)**: A scheduler will handle synchronization tasks with Google Calendar and Notion.

## License

This project is licensed under the MIT License.

---

Feel free to customize the description further based on your needs!
