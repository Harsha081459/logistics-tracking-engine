import mysql.connector
from datetime import datetime

# ====================== DATABASE CONNECTION ======================

def connect():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Harsha@1410",
            database="air_cargo",
            autocommit=False
        )
        print("Database connection established successfully")
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        return None

# ====================== CUSTOMER FUNCTIONS ======================

def register_customer(cursor, conn):
    print("\n===== Register New Customer =====")
    errors = []
    
    customer_id = input("Enter Customer ID (upto 10 characters): ").strip()
    name = input("Enter Full Name: ").strip()
    email = input("Enter Email (enter valid email format): ").strip()
    phone = input("Enter Phone (10 digits): ").strip()
    address = input("Enter Address: ").strip()

    if not customer_id:
        errors.append("Customer ID cannot be empty")
    else:
        cursor.execute("SELECT CustomerID FROM Customer WHERE CustomerID = %s", (customer_id,))
        if cursor.fetchone():
            errors.append("Customer ID already exists")

    if not name:
        errors.append("Name cannot be empty")

    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        errors.append("Invalid email format")
    else:
        cursor.execute("SELECT CustomerID FROM Customer WHERE Email = %s", (email.lower(),))
        if cursor.fetchone():
            errors.append("Email address already registered")

    if not (phone.isdigit() and len(phone) == 10):
        errors.append("Phone must be exactly 10 digits")
    else:
        cursor.execute("SELECT CustomerID FROM Customer WHERE Phone = %s", (phone,))
        if cursor.fetchone():
            errors.append("Phone number already registered")

    if not address:
        errors.append("Address cannot be empty")

    if errors:
        print("\nValidation Errors:")
        for error in errors:
            print(error)
        print("Registration rolled back due to errors")
        return None

    try:
        cursor.execute("""
            INSERT INTO Customer (CustomerID, Name, Email, Phone, Address)
            VALUES (%s, %s, %s, %s, %s)
        """, (customer_id, name, email, phone, address))
        conn.commit()
        print("\nAll data validated successfully!")
        print("Transaction committed successfully!")
        print(f"Customer '{name}' registered successfully!")
        return customer_id
    except mysql.connector.Error as err:
        print(f"\nDatabase Error: {err}")
        conn.rollback()
        print("Transaction rolled back due to database error")
        return None

def update_customer_address(cursor, conn):
    print("\n===== Update Customer Address =====")
    
    customer_id = input("Enter your Customer ID: ").strip()
    if not customer_id:
        print("Customer ID required")
        return

    try:
        cursor.execute("SELECT Name FROM Customer WHERE CustomerID = %s", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            print("Customer not found")
            return
            
        print(f"\nCurrent customer: {customer[0]}")
        
        new_address = input("Enter new address: ").strip()
        if not new_address:
            print("Address cannot be empty")
            return

        cursor.execute("""
            UPDATE Customer 
            SET Address = %s 
            WHERE CustomerID = %s
        """, (new_address, customer_id))
        
        conn.commit()
        print("\nAddress updated successfully!")
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"\nFailed to update address: {err}")
        print("Transaction rolled back")

def delete_customer(cursor, conn):
    print("\n===== Delete Customer Account =====")
    
    customer_id = input("Enter your Customer ID: ").strip()
    if not customer_id:
        print("Customer ID required")
        return

    try:
        cursor.execute("SELECT Name FROM Customer WHERE CustomerID = %s", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            print("Customer not found")
            return
            
        print(f"\nCustomer to delete: {customer[0]}")
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM Booking 
            WHERE CustomerID = %s 
            AND BookingStatus = 'Confirmed'
        """, (customer_id,))
        active_bookings = cursor.fetchone()[0]
        
        if active_bookings > 0:
            print(f"Cannot delete - customer has {active_bookings} active bookings")
            return

        confirm = input("\nAre you sure you want to delete this account? (yes/no): ").lower()
        if confirm != 'yes':
            print("Account deletion cancelled")
            return

        print("\nProcessing deletion...")
        cursor.execute("DELETE FROM Customer WHERE CustomerID = %s", (customer_id,))
        conn.commit()
        print("\nCustomer account deleted successfully!")
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"\nFailed to delete customer: {err}")
        print("Transaction rolled back")

def delete_booking(cursor, conn, customer_id):
    print("\n===== Delete Booking =====")
    
    try:
        cursor.execute("""
            SELECT b.BookingID, b.CargoID, f.AirportLocation, f.Destination, f.Date
            FROM Booking b
            JOIN Flight f ON b.FlightID = f.FlightID
            WHERE b.CustomerID = %s AND b.BookingStatus = 'Confirmed'
        """, (customer_id,))
        bookings = cursor.fetchall()
        
        if not bookings:
            print("\nNo active bookings found")
            return
            
        print("\nYour Active Bookings:")
        for i, (booking_id, cargo_id, source, dest, date) in enumerate(bookings, 1):
            print(f" {i}. Booking ID: {booking_id}")
            print(f"    Cargo ID: {cargo_id}")
            print(f"    Route: {source} -> {dest} on {date}")
            print("    ------------------------")
        
        while True:
            try:
                choice = int(input("\nSelect booking to delete (number): ").strip())
                if 1 <= choice <= len(bookings):
                    booking_id, cargo_id, _, _, _ = bookings[choice-1]
                    break
                print("Invalid selection")
            except ValueError:
                print("Please enter a number")

        confirm = input(f"\nAre you sure you want to delete booking {booking_id}? (yes/no): ").lower()
        if confirm != 'yes':
            print("Booking deletion cancelled")
            return

        cursor.execute("SELECT Weight FROM Cargo WHERE CargoID = %s", (cargo_id,))
        weight = cursor.fetchone()[0]

        print("\nProcessing deletion...")
        
        cursor.execute("SELECT FlightID FROM Booking WHERE BookingID = %s", (booking_id,))
        flight_id = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM Booking WHERE BookingID = %s", (booking_id,))
        cursor.execute("DELETE FROM Cargo WHERE CargoID = %s", (cargo_id,))
        cursor.execute("""
            UPDATE Flight 
            SET AvailableSpace = AvailableSpace + %s 
            WHERE FlightID = %s
        """, (weight, flight_id))
        
        conn.commit()
        print("\nBooking deleted successfully!")
        print(f"Freed {weight}kg on flight {flight_id}")
        
    except mysql.connector.Error as err:
        conn.rollback()
        print(f"\nFailed to delete booking: {err}")
        print("Transaction rolled back")

def book_cargo(cursor, conn, customer_id):
    print("\n===== Book Cargo Shipment =====")
    
    try:
        cursor.execute("""
            SELECT f.FlightID, f.AirportLocation, f.Destination, f.Date, f.AvailableSpace
            FROM Flight f
            WHERE f.AvailableSpace > 0 AND f.Date >= CURDATE()
            ORDER BY f.Date, f.AirportLocation
        """)
        flights = cursor.fetchall()
        
        if not flights:
            print("\nNo available flights at this time.")
            return
        
        print("\nAvailable Flights:")
        for i, (fid, source, dest, date, space) in enumerate(flights, start=1):
            print(f" {i}. {source} -> {dest} | {date} | Space: {space}kg")
        
        print(f" {len(flights)+1}. Cancel booking")

        while True:
            choice = input("\nSelect flight (number): ").strip()
            try:
                choice = int(choice)
                if choice == len(flights)+1:
                    return
                if 1 <= choice <= len(flights):
                    flight_id, source, dest, date, space = flights[choice-1]
                    break
                print("Invalid selection")
            except ValueError:
                print("Please enter a number")

        while True:
            cargo_id = input("\nEnter Cargo ID: ").strip()
            if not cargo_id:
                print("Cargo ID required")
                continue
                
            cursor.execute("SELECT CargoID FROM Cargo WHERE CargoID = %s", (cargo_id,))
            if cursor.fetchone():
                print("Cargo ID already exists")
                continue
            break

        while True:
            try:
                weight = float(input("Enter weight (kg): "))
                if weight <= 0:
                    print("Weight must be positive")
                    continue
                if weight > space:
                    print(f"Only {space}kg available")
                    continue
                break
            except ValueError:
                print("Enter a valid number")

        while True:
            cargo_type = input("Enter cargo type: ").strip()
            if not cargo_type:
                print("Cargo type required")
                continue
            break

        cursor.execute("SELECT MAX(BookingID) FROM Booking")
        last_id = cursor.fetchone()[0]
        booking_id = f"BKG{int(last_id[3:])+1:03}" if last_id else "BKG001"

        try:
            print("\nProcessing transaction...")
            cursor.execute("""
                INSERT INTO Cargo (CargoID, Weight, CargoType, TrackingStatus, LastUpdated, Location)
                VALUES (%s, %s, %s, 'Booked', NOW(), %s)
            """, (cargo_id, weight, cargo_type, source))

            cursor.execute("""
                INSERT INTO Booking (BookingID, CargoID, CustomerID, FlightID, BookingDate, BookingStatus)
                VALUES (%s, %s, %s, %s, NOW(), 'Confirmed')
            """, (booking_id, cargo_id, customer_id, flight_id))

            cursor.execute("""
                UPDATE Flight SET AvailableSpace = AvailableSpace - %s
                WHERE FlightID = %s
            """, (weight, flight_id))

            conn.commit()
            print("\nTransaction committed successfully!")
            print("\nBooking Successful!")
            print(f"Booking ID: {booking_id}")
            print(f"Flight: {source} -> {dest} on {date}")
            print(f"Cargo: {cargo_id} ({weight}kg of {cargo_type})")

        except mysql.connector.Error as err:
            conn.rollback()
            print(f"\nTransaction failed: {err}")
            print("Transaction rolled back due to errors")

    except Exception as e:
        print(f"\nSystem Error: {e}")
        conn.rollback()
        print("Transaction rolled back due to system error")

# ====================== EMPLOYEE FUNCTIONS ======================

def update_cargo_status(cursor, conn):
    print("\n===== Update Cargo Status =====")
    
    while True:
        cargo_id = input("Enter Cargo ID: ").strip()
        if not cargo_id:
            print("Cargo ID required")
            continue
        break

    try:
        cursor.execute("""
            SELECT c.TrackingStatus, c.Weight, b.FlightID, f.Destination, b.BookingID
            FROM Cargo c
            JOIN Booking b ON c.CargoID = b.CargoID
            JOIN Flight f ON b.FlightID = f.FlightID
            WHERE c.CargoID = %s
        """, (cargo_id,))
        result = cursor.fetchone()

        if not result:
            print("Cargo not found")
            return

        status, weight, flight_id, destination, booking_id = result

        if status == 'Delivered':
            print("Cargo already delivered")
            return

        confirm = input(f"Mark {cargo_id} as delivered to {destination}? (yes/no): ").lower()
        if confirm != 'yes':
            print("Update cancelled")
            return

        print("\nProcessing transaction...")
        
        # Update cargo status
        cursor.execute("""
            UPDATE Cargo 
            SET TrackingStatus = 'Delivered', 
                LastUpdated = NOW(), 
                Location = %s
            WHERE CargoID = %s
        """, (destination, cargo_id))

        # Update flight space
        cursor.execute("""
            UPDATE Flight 
            SET AvailableSpace = AvailableSpace + %s 
            WHERE FlightID = %s
        """, (weight, flight_id))

        # Delete the booking record
        cursor.execute("DELETE FROM Booking WHERE BookingID = %s", (booking_id,))

        conn.commit()
        print("\nTransaction committed successfully!")
        print(f"\n{cargo_id} marked as delivered")
        print(f"Restored {weight}kg to flight {flight_id}")
        print(f"Booking {booking_id} automatically deleted")

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"\nTransaction failed: {err}")
        print("Transaction rolled back due to errors")

def track_cargo(cursor):
    print("\n===== Track Cargo Status =====")
    
    cargo_id = input("Enter Cargo ID: ").strip()
    if not cargo_id:
        print("Cargo ID required")
        return

    try:
        cursor.execute("""
            SELECT TrackingStatus, Location, LastUpdated
            FROM Cargo WHERE CargoID = %s
        """, (cargo_id,))
        cargo = cursor.fetchone()

        if not cargo:
            print("Cargo not found")
            return

        status, location, updated = cargo

        cursor.execute("""
            SELECT f.FlightID, f.AirportLocation, f.Destination, f.Date
            FROM Booking b
            JOIN Flight f ON b.FlightID = f.FlightID
            WHERE b.CargoID = %s
        """, (cargo_id,))
        flight = cursor.fetchone()

        print("\nCargo Details:")
        print(f"Status: {status}")
        print(f"Location: {location}")
        print(f"Last Updated: {updated}")

        if flight:
            print("\nFlight Details:")
            print(f"Flight ID: {flight[0]}")
            print(f"Route: {flight[1]} -> {flight[2]}")
            print(f"Date: {flight[3]}")

    except mysql.connector.Error as err:
        print(f"\nTracking failed: {err}")

def check_flights(cursor):
    print("\n===== Check Flights Availability =====")
    
    source = input("From (leave blank for all): ").strip()
    destination = input("To (leave blank for all): ").strip()
    date = input("Date (YYYY-MM-DD, leave blank for all): ").strip()

    query = """
        SELECT FlightID, AirportLocation, Destination, Date, AvailableSpace 
        FROM Flight 
        WHERE AvailableSpace > 0 AND Date >= CURDATE()
    """
    params = []

    if source:
        query += " AND LOWER(AirportLocation) = LOWER(%s)"
        params.append(source)
    if destination:
        query += " AND LOWER(Destination) = LOWER(%s)"
        params.append(destination)
    if date:
        query += " AND Date = %s"
        params.append(date)

    query += " ORDER BY Date, AirportLocation"

    try:
        cursor.execute(query, tuple(params))
        flights = cursor.fetchall()

        if not flights:
            print("\nNo flights found")
            return

        print("\nAvailable Flights:")
        for flight in flights:
            print(f"{flight[0]}: {flight[1]} -> {flight[2]} | {flight[3]} | Space: {flight[4]}kg")

    except mysql.connector.Error as err:
        print(f"\nSearch failed: {err}")

# ====================== MENUS ======================

def customer_menu(cursor, conn):
    customer_id = None
    
    while True:
        print("\n===== Customer Menu =====")
        print("1. Existing Customer Login")
        print("2. New Customer Registration")
        print("3. Back")
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            customer_id = input("Enter your Customer ID: ").strip()
            if not customer_id:
                print("Customer ID required")
                continue
                
            cursor.execute("SELECT Name FROM Customer WHERE CustomerID = %s", (customer_id,))
            customer = cursor.fetchone()
            
            if not customer:
                print("Customer not found")
                continue
                
            print(f"\nWelcome back, {customer[0]}!")
            logged_in_menu(cursor, conn, customer_id)
            customer_id = None
            
        elif choice == "2":
            customer_id = register_customer(cursor, conn)
            if customer_id:
                logged_in_menu(cursor, conn, customer_id)
                customer_id = None
                
        elif choice == "3":
            break
            
        else:
            print("Invalid option")

def logged_in_menu(cursor, conn, customer_id):
    while True:
        print("\n===== Customer Dashboard =====")
        print(f"Logged in as: {customer_id}")
        print("1. Book Cargo")
        print("2. Update Address")
        print("3. Delete Booking")
        print("4. Delete Account")
        print("5. Logout")
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            book_cargo(cursor, conn, customer_id)
        elif choice == "2":
            update_customer_address(cursor, conn)
        elif choice == "3":
            delete_booking(cursor, conn, customer_id)
        elif choice == "4":
            delete_customer(cursor, conn)
            break
        elif choice == "5":
            print("\nLogged out successfully!")
            break
        else:
            print("Invalid option")

def employee_menu(cursor, conn):
    while True:
        print("\n===== Employee Menu =====")
        print("1. Update Cargo Status")
        print("2. Track Cargo")
        print("3. Check Flights")
        print("4. Back")
        
        choice = input("Select option: ").strip()
        
        if choice == "1":
            update_cargo_status(cursor, conn)
        elif choice == "2":
            track_cargo(cursor)
        elif choice == "3":
            check_flights(cursor)
        elif choice == "4":
            break
        else:
            print("Invalid option")

# ====================== MAIN ======================

def main():
    conn = connect()
    if not conn:
        return

    cursor = conn.cursor()

    try:
        while True:
            print("\n===== Air-Travel Cargo Services =====")
            print("1. Customer")
            print("2. Employee")
            print("3. Exit")
            
            role = input("Select role: ").strip()
            
            if role == "1":
                customer_menu(cursor, conn)
            elif role == "2":
                employee_menu(cursor, conn)
            elif role == "3":
                print("\nThank you for using our services!")
                break
            else:
                print("Invalid option")
                
    except Exception as e:
        print(f"\nSystem error: {e}")
        conn.rollback()
        print("Transaction rolled back due to system error")
    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed")

if __name__ == "__main__":
    main()
