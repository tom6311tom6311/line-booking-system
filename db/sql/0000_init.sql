-- Create Enums
CREATE TYPE room_statuses AS ENUM ('available', 'closed');
CREATE TYPE booking_sources AS ENUM ('direct', 'Booking.com', 'FB', 'Expedia', 'Taiwanstay', 'Airbnb');
CREATE TYPE booking_statuses AS ENUM ('new', 'prepaid', 'canceled');


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
    room_name VARCHAR(100) PRIMARY KEY,
    room_number INT NOT NULL,
    room_type VARCHAR(50),
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
    customer_id INT REFERENCES Customers(customer_id),
    check_in_date DATE NOT NULL,
    last_date DATE NOT NULL,
    total_price DECIMAL(10, 2),
    prepayment DECIMAL(10, 2),
    prepayment_note TEXT,
    source booking_sources,
    status booking_statuses,
    notes TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create RoomBooking junction table for many-to-many relationship between Bookings and Rooms
CREATE TABLE RoomBookings (
    booking_id INT REFERENCES Bookings(booking_id) ON DELETE CASCADE,
    room_name VARCHAR(100) REFERENCES Rooms(room_name) ON DELETE CASCADE,
    PRIMARY KEY (booking_id, room_name),
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create RoomClosure table
CREATE TABLE RoomClosures (
    room_closure_id SERIAL PRIMARY KEY,
    room_name VARCHAR(100) REFERENCES Rooms(room_name) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    last_date DATE NOT NULL,
    reason TEXT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
