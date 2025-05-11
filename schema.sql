-- =================================================================================
-- Air-Travel Cargo Services - Database Schema
-- Database: air_cargo
-- =================================================================================

CREATE DATABASE IF NOT EXISTS air_cargo;
USE air_cargo;

-- Drop tables if they exist to prevent conflicts during testing
DROP TABLE IF EXISTS Booking;
DROP TABLE IF EXISTS Cargo;
DROP TABLE IF EXISTS Flight;
DROP TABLE IF EXISTS Customer;

-- =================================================================================
-- 1. CREATE TABLES
-- =================================================================================

-- Customer Table
CREATE TABLE Customer (
    CustomerID VARCHAR(10) PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    Phone VARCHAR(10) UNIQUE NOT NULL,
    Address VARCHAR(255) NOT NULL
);

-- Flight Table
CREATE TABLE Flight (
    FlightID VARCHAR(10) PRIMARY KEY,
    AirportLocation VARCHAR(100) NOT NULL,
    Destination VARCHAR(100) NOT NULL,
    Date DATE NOT NULL,
    AvailableSpace FLOAT NOT NULL
);

-- Cargo Table
CREATE TABLE Cargo (
    CargoID VARCHAR(20) PRIMARY KEY,
    Weight FLOAT NOT NULL,
    CargoType VARCHAR(50) NOT NULL,
    TrackingStatus VARCHAR(50) NOT NULL DEFAULT 'Booked',
    LastUpdated DATETIME NOT NULL,
    Location VARCHAR(100) NOT NULL
);

-- Booking Table
CREATE TABLE Booking (
    BookingID VARCHAR(20) PRIMARY KEY,
    CargoID VARCHAR(20) NOT NULL,
    CustomerID VARCHAR(10) NOT NULL,
    FlightID VARCHAR(10) NOT NULL,
    BookingDate DATETIME NOT NULL,
    BookingStatus VARCHAR(20) NOT NULL DEFAULT 'Confirmed',
    FOREIGN KEY (CargoID) REFERENCES Cargo(CargoID) ON DELETE CASCADE,
    FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID) ON DELETE CASCADE,
    FOREIGN KEY (FlightID) REFERENCES Flight(FlightID) ON DELETE CASCADE
);

-- =================================================================================
-- 2. SEED DUMMY DATA (Flights are required to book cargo)
-- =================================================================================

-- Seed upcoming flights so customers have options to book
INSERT INTO Flight (FlightID, AirportLocation, Destination, Date, AvailableSpace) VALUES 
('FL-101', 'New York (JFK)', 'London (LHR)', DATE_ADD(CURDATE(), INTERVAL 2 DAY), 5000.0),
('FL-202', 'Singapore (SIN)', 'Frankfurt (FRA)', DATE_ADD(CURDATE(), INTERVAL 3 DAY), 10000.0),
('FL-303', 'London (LHR)', 'Dubai (DXB)', DATE_ADD(CURDATE(), INTERVAL 5 DAY), 7500.0),
('FL-404', 'Los Angeles (LAX)', 'Tokyo (NRT)', DATE_ADD(CURDATE(), INTERVAL 1 DAY), 2500.0),
('FL-505', 'Frankfurt (FRA)', 'New York (JFK)', DATE_ADD(CURDATE(), INTERVAL 4 DAY), 8000.0);

-- Seed a sample customer
INSERT INTO Customer (CustomerID, Name, Email, Phone, Address) VALUES 
('CUST001', 'Acme Corp', 'shipping@acme.com', '1234567890', '123 Business Rd, New York');
