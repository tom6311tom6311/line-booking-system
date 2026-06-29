# Line Booking System

This project is a microservices-based **Room Booking Management System** built with Docker Compose. It includes a **PostgreSQL database** and a **Python-Flask LINE bot server** to facilitate booking creation, updates, and synchronization with external systems like **Google Calendar** and **Notion**.

## Features

- **Microservices Architecture**: Services are containerized using Docker.
- **PostgreSQL Database**: Stores booking data and related information.
- **LINE Bot Integration**: Admins and stakeholders interact with the system via a LINE bot.
- **Synchronization**: Bookings are synchronized with Google Calendar and Notion.

## Project Structure

```
/project-root
│
├── /db                    # PostgreSQL service
├── /line-bot-server        # Python-Flask LINE bot service
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
DB_HOST=db
DB_PORT=5432
DB_USER=YOUR_DB_USER
DB_PASSWORD=YOUR_DB_PASSWORD
DB_NAME=YOUR_DB_NAME
DB_SSLMODE=
DB_SSLROOTCERT=
```

For local Docker development, keep `DB_HOST=db` and run the full Compose stack.

For AWS RDS, set `DB_HOST` to the RDS endpoint, keep `DB_PORT=5432`, and set `DB_SSLMODE=verify-full` if you want certificate hostname verification. Download the AWS RDS CA bundle as `certs/global-bundle.pem` and set `DB_SSLROOTCERT=/app/certs/global-bundle.pem`.

Start only the app services so the local database container is not used:

```bash
docker-compose up --build line-bot-server scheduler
```

## How It Works

- **LINE Bot Server**: Admins can interact with the system via the LINE bot, handling booking creation, updates, and more.
- **PostgreSQL**: The database stores all booking-related data, including customer info, rooms, and booking status.
- **Scheduler (Future Implementation)**: A scheduler will handle synchronization tasks with Google Calendar and Notion.

## License

This project is licensed under the MIT License.

---

Feel free to customize the description further based on your needs!
