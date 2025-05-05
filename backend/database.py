import os
import mysql.connector
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "Harsha@1410"),
            database=os.getenv("DB_NAME", "air_cargo"),
            autocommit=False
        )
        return conn
    except mysql.connector.Error as err:
        raise Exception(f"Database connection failed: {err}")

# Customer Operations with Passwords
def register_customer(customer_id, name, email, phone, address, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        hashed_password = pwd_context.hash(password)
        cursor.execute(
            "INSERT INTO Customer (CustomerID, Name, Email, Phone, Address, PasswordHash) VALUES (%s, %s, %s, %s, %s, %s)",
            (customer_id, name, email, phone, address, hashed_password)
        )
        conn.commit()
        return customer_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def login_customer(customer_id, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Customer WHERE CustomerID = %s", (customer_id,))
        customer = cursor.fetchone()
        if not customer:
            raise ValueError("Customer not found")
        if not pwd_context.verify(password, customer['PasswordHash']):
            raise ValueError("Incorrect password")
        
        # Remove hash from dict before returning to API
        del customer['PasswordHash']
        return customer
    finally:
        cursor.close()
        conn.close()

def get_customer_by_id(customer_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT CustomerID, Name, Email, Phone, Address FROM Customer WHERE CustomerID = %s", (customer_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

# Flight/Route Operations
def check_routes():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT FlightID, OriginHub, DestinationHub, DepartureDate, AvailableCapacity FROM Flight WHERE AvailableCapacity > 0 AND DepartureDate >= CURDATE()")
        flights = cursor.fetchall()
        for f in flights:
            f['DepartureDate'] = str(f['DepartureDate'])
        return flights
    finally:
        cursor.close()
        conn.close()

# Pricing Engine
def calculate_price(weight, cargo_type):
    base_rate = 5.0 # $5 per kg
    cost = weight * base_rate
    if cargo_type.lower() in ['hazardous', 'perishable', 'electronics']:
        cost *= 1.25 # 25% surcharge
    return round(cost, 2)

# Booking & Tracking
def book_cargo(customer_id, flight_id, cargo_id, weight, cargo_type):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT OriginHub, AvailableCapacity FROM Flight WHERE FlightID = %s AND AvailableCapacity >= %s", (flight_id, weight))
        flight = cursor.fetchone()
        if not flight:
            raise ValueError("Flight not available or insufficient capacity")

        total_cost = calculate_price(weight, cargo_type)
        origin_hub = flight['OriginHub']

        cursor.execute("""
            INSERT INTO Cargo (TrackingNumber, Weight, CargoType, TotalCost, CurrentStatus, CurrentLocation)
            VALUES (%s, %s, %s, %s, 'Label Created', %s)
        """, (cargo_id, weight, cargo_type, total_cost, origin_hub))

        cursor.execute("""
            INSERT INTO TrackingHistory (TrackingNumber, Status, Location, Remarks)
            VALUES (%s, 'Label Created', %s, 'Shipment booked by customer')
        """, (cargo_id, origin_hub))

        cursor.execute("SELECT MAX(CAST(SUBSTRING(BookingID, 4) AS UNSIGNED)) as last_id FROM Booking")
        result = cursor.fetchone()
        new_id = (result['last_id'] or 0) + 1
        booking_id = f"BKG{new_id:03}"

        cursor.execute("""
            INSERT INTO Booking (BookingID, TrackingNumber, CustomerID, FlightID)
            VALUES (%s, %s, %s, %s)
        """, (booking_id, cargo_id, customer_id, flight_id))

        cursor.execute("UPDATE Flight SET AvailableCapacity = AvailableCapacity - %s WHERE FlightID = %s", (weight, flight_id))

        conn.commit()
        return {"BookingID": booking_id, "TrackingNumber": cargo_id, "TotalCost": total_cost}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_tracking_timeline(tracking_number):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM Cargo WHERE TrackingNumber = %s", (tracking_number,))
        cargo = cursor.fetchone()
        if not cargo:
            raise ValueError("Tracking Number not found")

        cursor.execute("SELECT Status, Location, Timestamp, Remarks FROM TrackingHistory WHERE TrackingNumber = %s ORDER BY Timestamp ASC", (tracking_number,))
        history = cursor.fetchall()
        for h in history:
            h['Timestamp'] = str(h['Timestamp'])
            
        return {"cargo": cargo, "timeline": history}
    finally:
        cursor.close()
        conn.close()

def update_tracking_status(tracking_number, new_status, location, remarks):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT CurrentStatus FROM Cargo WHERE TrackingNumber = %s", (tracking_number,))
        cargo = cursor.fetchone()
        if not cargo:
            raise ValueError("Cargo not found")
        if cargo['CurrentStatus'] == 'Delivered':
            raise ValueError("Cargo is already marked as Delivered")

        cursor.execute("UPDATE Cargo SET CurrentStatus = %s, CurrentLocation = %s WHERE TrackingNumber = %s", (new_status, location, tracking_number))

        cursor.execute("INSERT INTO TrackingHistory (TrackingNumber, Status, Location, Remarks) VALUES (%s, %s, %s, %s)", (tracking_number, new_status, location, remarks))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def get_customer_bookings(customer_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT b.BookingID, c.TrackingNumber, c.CurrentStatus, c.TotalCost, f.OriginHub, f.DestinationHub 
            FROM Booking b
            JOIN Cargo c ON b.TrackingNumber = c.TrackingNumber
            JOIN Flight f ON b.FlightID = f.FlightID
            WHERE b.CustomerID = %s
        """, (customer_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
