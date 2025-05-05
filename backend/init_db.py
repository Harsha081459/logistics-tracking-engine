import mysql.connector
import random

def initialize_database():
    print("Connecting to MySQL server...")
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Harsha@1410"
        )
        cursor = conn.cursor()
        
        cursor.execute("CREATE DATABASE IF NOT EXISTS air_cargo")
        cursor.execute("USE air_cargo")
        
        print("Dropping existing tables to apply new schema...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS TrackingHistory, Booking, Cargo, Flight, Customer")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        print("Creating tables...")
        # Customer Table
        cursor.execute("""
            CREATE TABLE Customer (
                CustomerID VARCHAR(20) PRIMARY KEY,
                Name VARCHAR(100) NOT NULL,
                Email VARCHAR(100) UNIQUE NOT NULL,
                Phone VARCHAR(10) UNIQUE NOT NULL,
                Address TEXT NOT NULL,
                PasswordHash VARCHAR(255) NOT NULL
            )
        """)

        # Flight / Route Table
        cursor.execute("""
            CREATE TABLE Flight (
                FlightID VARCHAR(20) PRIMARY KEY,
                OriginHub VARCHAR(100) NOT NULL,
                DestinationHub VARCHAR(100) NOT NULL,
                DepartureDate DATE NOT NULL,
                AvailableCapacity FLOAT NOT NULL
            )
        """)

        # Cargo Package Table
        cursor.execute("""
            CREATE TABLE Cargo (
                TrackingNumber VARCHAR(20) PRIMARY KEY,
                Weight FLOAT NOT NULL,
                CargoType VARCHAR(50) NOT NULL,
                TotalCost FLOAT NOT NULL,
                CurrentStatus VARCHAR(50) NOT NULL,
                CurrentLocation VARCHAR(100)
            )
        """)

        # Tracking History (1-to-Many Relationship)
        cursor.execute("""
            CREATE TABLE TrackingHistory (
                UpdateID INT AUTO_INCREMENT PRIMARY KEY,
                TrackingNumber VARCHAR(20) NOT NULL,
                Status VARCHAR(50) NOT NULL,
                Location VARCHAR(100) NOT NULL,
                Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                Remarks TEXT,
                FOREIGN KEY (TrackingNumber) REFERENCES Cargo(TrackingNumber) ON DELETE CASCADE
            )
        """)

        # Booking Table
        cursor.execute("""
            CREATE TABLE Booking (
                BookingID VARCHAR(20) PRIMARY KEY,
                TrackingNumber VARCHAR(20),
                CustomerID VARCHAR(20),
                FlightID VARCHAR(20),
                BookingDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (TrackingNumber) REFERENCES Cargo(TrackingNumber) ON DELETE CASCADE,
                FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE,
                FOREIGN KEY (FlightID) REFERENCES Flight(FlightID) ON DELETE CASCADE
            )
        """)
        
        print("Adding some sample logistics routes...")
        cursor.execute("""
            INSERT INTO Flight (FlightID, OriginHub, DestinationHub, DepartureDate, AvailableCapacity) VALUES 
            ('RT-NY-LDN', 'New York Hub', 'London Hub', DATE_ADD(CURDATE(), INTERVAL 1 DAY), 5000),
            ('RT-LA-TOK', 'Los Angeles Hub', 'Tokyo Hub', DATE_ADD(CURDATE(), INTERVAL 3 DAY), 8000),
            ('RT-LDN-DUB', 'London Hub', 'Dubai Hub', DATE_ADD(CURDATE(), INTERVAL 2 DAY), 2500)
        """)

        conn.commit()
        print("Database and tables created successfully!")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    initialize_database()
