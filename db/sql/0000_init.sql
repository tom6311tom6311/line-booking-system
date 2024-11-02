-- Create Enums
CREATE TYPE room_types AS ENUM ('standard_double_room', 'standard_family_room', 'economic_family_room', 'backpacker_bed', 'washitsu', 'grass');
CREATE TYPE room_statuses AS ENUM ('available', 'closed');
CREATE TYPE booking_sources AS ENUM ('自洽', 'Booking_com', 'FB', 'Agoda', '台灣旅宿', 'Airbnb');
CREATE TYPE booking_statuses AS ENUM ('new', 'prepaid', 'canceled');
CREATE TYPE prepayment_statuses AS ENUM ('unpaid', 'paid', 'refunded', 'hanging');
CREATE TYPE sync_types AS ENUM ('sql_to_google_calendar', 'sql_to_notion', 'notion_to_sql');


-- Create Customers table
CREATE TABLE Customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone_number VARCHAR(20),
    address VARCHAR(255),
    relationship VARCHAR(100),
    notes TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Rooms table
CREATE TABLE Rooms (
    room_id VARCHAR(1) PRIMARY KEY,
    room_name VARCHAR(100) UNIQUE,
    room_count INT NOT NULL,
    room_type room_types,
    capacity INT NOT NULL,
    holiday_price_per_night DECIMAL(10, 2),
    weekday_price_per_night DECIMAL(10, 2),
    extra_bed_number INT NOT NULL,
    description TEXT,
    room_status room_statuses,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Bookings table
CREATE TABLE Bookings (
    booking_id SERIAL PRIMARY KEY,
    status booking_statuses,
    customer_id INT REFERENCES Customers(customer_id),
    check_in_date DATE NOT NULL,
    last_date DATE NOT NULL,
    total_price DECIMAL(10, 2),
    prepayment DECIMAL(10, 2),
    prepayment_note TEXT,
    prepayment_status prepayment_statuses,
    source booking_sources,
    notes TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create RoomBooking junction table for many-to-many relationship between Bookings and Rooms
CREATE TABLE RoomBookings (
    booking_id INT REFERENCES Bookings(booking_id) ON DELETE CASCADE,
    room_id VARCHAR(100) REFERENCES Rooms(room_id) ON DELETE CASCADE,
    PRIMARY KEY (booking_id, room_id),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create RoomClosure table
CREATE TABLE RoomClosures (
    room_closure_id SERIAL PRIMARY KEY,
    room_id VARCHAR(100) REFERENCES Rooms(room_id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    last_date DATE NOT NULL,
    reason TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create SyncRecord table
CREATE TABLE SyncRecords (
    sync_id SERIAL PRIMARY KEY,
    sync_type sync_types,
    synced_booking_ids TEXT NOT NULL,  -- Stores booking IDs as a comma-separated string or JSON array
    success BOOLEAN NOT NULL,
    error_message TEXT,  -- Optional column to store any error messages if the sync fails
    synced_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create a function to automatically update the modified column
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.modified = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to the Customers table
CREATE TRIGGER trigger_update_customers
BEFORE UPDATE ON Customers
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Apply the trigger to the Rooms table
CREATE TRIGGER trigger_update_rooms
BEFORE UPDATE ON Rooms
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Apply the trigger to the Bookings table
CREATE TRIGGER trigger_update_bookings
BEFORE UPDATE ON Bookings
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Apply the trigger to the RoomBookings table
CREATE TRIGGER trigger_update_room_bookings
BEFORE UPDATE ON RoomBookings
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- Apply the trigger to the RoomClosures table
CREATE TRIGGER trigger_update_room_closures
BEFORE UPDATE ON RoomClosures
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();
