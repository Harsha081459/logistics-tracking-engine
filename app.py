from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import mysql.connector
import os
from datetime import datetime
from typing import Optional

app = FastAPI(
    title="Air-Travel Cargo Services API",
    description="RESTful logistics API with ACID transactions and RBAC",
    version="1.0.0"
)

# ====================== DATABASE CONNECTION ======================
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "air_cargo"),
            autocommit=False
        )
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {err}")

# ====================== MOCK JWT AUTH ======================
def verify_jwt_token(authorization: str = Header(...)):
    # Mock JWT verification for demonstration purposes
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    token = authorization.split(" ")[1]
    if token != "mock-jwt-admin-token-123":
        raise HTTPException(status_code=403, detail="Invalid or expired JWT token")
    return {"role": "admin"}

# ====================== SCHEMAS ======================
class CargoCreate(BaseModel):
    tracking_number: str
    weight: float
    cargo_type: str
    total_cost: float
    current_status: str
    current_location: str
    customer_id: str
    flight_id: str

# ====================== ENDPOINTS ======================

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "air-cargo-api"}

@app.get("/shipments/{tracking_id}")
def get_shipment_details(tracking_id: str, user: dict = Depends(verify_jwt_token)):
    """
    GET /shipments/{id} with JOIN queries to fetch cargo, customer, and flight details.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
            SELECT 
                c.TrackingNumber, c.Weight, c.CargoType, c.CurrentStatus, c.CurrentLocation,
                cust.Name AS CustomerName, cust.Email,
                f.FlightID, f.OriginHub, f.DestinationHub, f.DepartureDate,
                b.BookingDate
            FROM cargo c
            LEFT JOIN booking b ON c.TrackingNumber = b.TrackingNumber
            LEFT JOIN customer cust ON b.CustomerID = cust.CustomerID
            LEFT JOIN flight f ON b.FlightID = f.FlightID
            WHERE c.TrackingNumber = %s
        """
        cursor.execute(query, (tracking_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Shipment not found")
            
        return {"data": result}
    finally:
        cursor.close()
        conn.close()

@app.post("/cargo", status_code=201)
def create_cargo(cargo: CargoCreate, user: dict = Depends(verify_jwt_token)):
    """
    POST /cargo with strict ACID transaction management across multiple tables.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Step 1: Insert into Cargo
        cursor.execute("""
            INSERT INTO cargo (TrackingNumber, Weight, CargoType, TotalCost, CurrentStatus, CurrentLocation)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (cargo.tracking_number, cargo.weight, cargo.cargo_type, cargo.total_cost, cargo.current_status, cargo.current_location))
        
        # Step 2: Create Booking mapping
        booking_id = f"BKG-{cargo.tracking_number[-4:]}-{datetime.now().strftime('%M%S')}"
        cursor.execute("""
            INSERT INTO booking (BookingID, TrackingNumber, CustomerID, FlightID)
            VALUES (%s, %s, %s, %s)
        """, (booking_id, cargo.tracking_number, cargo.customer_id, cargo.flight_id))
        
        # Step 3: Insert Initial Tracking History
        cursor.execute("""
            INSERT INTO trackinghistory (TrackingNumber, Status, Location, Remarks)
            VALUES (%s, %s, %s, %s)
        """, (cargo.tracking_number, cargo.current_status, cargo.current_location, "Initial cargo booking via API"))
        
        # If all successful, commit transaction (ACID)
        conn.commit()
        
        return {
            "message": "Cargo created successfully", 
            "tracking_number": cargo.tracking_number,
            "booking_id": booking_id
        }
        
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Transaction Failed. Rolled back: {err}")
    finally:
        cursor.close()
        conn.close()
