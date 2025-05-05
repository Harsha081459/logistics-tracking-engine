import os
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Body, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.database import (
    register_customer, login_customer, check_routes, calculate_price, book_cargo,
    get_tracking_timeline, update_tracking_status, get_customer_bookings, get_customer_by_id
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Global Logistics Tracking Platform API with JWT")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key")
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=2)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        customer_id: str = payload.get("sub")
        if customer_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return customer_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))

class CustomerRegister(BaseModel):
    customer_id: str
    name: str
    email: str
    phone: str
    address: str
    password: str

class CustomerLogin(BaseModel):
    customer_id: str
    password: str

class BookingRequest(BaseModel):
    flight_id: str
    cargo_id: str
    weight: float
    cargo_type: str

class TrackingUpdate(BaseModel):
    status: str
    location: str
    remarks: str

# --- Auth Endpoints ---
@app.post("/api/auth/register")
def api_register_customer(customer: CustomerRegister):
    try:
        register_customer(customer.customer_id, customer.name, customer.email, customer.phone, customer.address, customer.password)
        return {"message": "Customer registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
def api_login_customer(creds: CustomerLogin):
    try:
        customer = login_customer(creds.customer_id, creds.password)
        access_token = create_access_token(data={"sub": customer["CustomerID"]})
        return {"access_token": access_token, "token_type": "bearer", "customer": customer}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# --- Secure Customer Endpoints ---
@app.get("/api/customers/me")
def api_get_me(current_customer_id: str = Depends(get_current_user)):
    return get_customer_by_id(current_customer_id)

@app.get("/api/customers/me/bookings")
def api_get_my_bookings(current_customer_id: str = Depends(get_current_user)):
    return get_customer_bookings(current_customer_id)

@app.post("/api/customers/me/bookings")
def api_book_cargo(booking: BookingRequest, current_customer_id: str = Depends(get_current_user)):
    try:
        result = book_cargo(current_customer_id, booking.flight_id, booking.cargo_id, booking.weight, booking.cargo_type)
        return {"message": "Booking successful", "details": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Public Endpoints ---
@app.get("/api/flights")
def api_check_flights():
    return check_routes()

@app.post("/api/pricing")
def api_calculate_pricing(weight: float = Body(...), cargo_type: str = Body(...)):
    return {"total_cost": calculate_price(weight, cargo_type)}

@app.get("/api/tracking/{tracking_number}")
def api_track_package(tracking_number: str):
    try:
        return get_tracking_timeline(tracking_number)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/tracking/{tracking_number}/update")
def api_update_tracking(tracking_number: str, update: TrackingUpdate):
    try:
        update_tracking_status(tracking_number, update.status, update.location, update.remarks)
        return {"message": "Tracking history updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
