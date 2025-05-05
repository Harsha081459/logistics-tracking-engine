# Global Logistics Tracking Platform

An enterprise-grade logistics and cargo tracking application. This platform simulates a real-world supply chain engine (similar to DHL or FedEx) featuring dynamic pricing, a visual package tracking timeline, and Role-Based Access Control (RBAC).

## Features
- **Visual Tracking Timeline:** Customers can track their packages using a unique tracking number to see a visual timeline of the package's journey across hubs.
- **Dynamic Pricing Engine:** Shipping costs are automatically calculated based on weight and cargo type (Hazardous, Perishable, Electronics).
- **JWT Authentication:** Secure user registration and login using `bcrypt` password hashing and JSON Web Tokens.
- **Role-Based Access:** 
  - **Customers:** Register, book shipments, and view personal booking history.
  - **Employees/Hub Workers:** Scan packages and update their tracking status (e.g., *In Transit*, *Delivered*).

## Tech Stack
- **Backend:** Python, FastAPI, Passlib, PyJWT
- **Database:** MySQL 8.0 (Relational Database with 1-to-many Tracking History mapping)
- **Frontend:** HTML5, Vanilla JavaScript, CSS3 (Glassmorphism design)
- **Deployment:** Docker, Docker Compose

## Project Structure
```
/backend            # FastAPI server and MySQL database controllers
/frontend           # Static web files (HTML/CSS/JS)
.env                # Environment secrets
requirements.txt    # Python dependencies
docker-compose.yml  # Container orchestration script
Dockerfile          # Backend container builder
```

## Running the Application Locally (Without Docker)

1. **Install MySQL:** Ensure MySQL is installed and running on your local machine.
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Environment:** Update the `.env` file with your local MySQL credentials.
4. **Initialize Database:**
   ```bash
   python backend/init_db.py
   ```
5. **Start the Server:**
   ```bash
   uvicorn backend.api:app --reload
   ```
6. Open your browser to `http://127.0.0.1:8000/`.

## Running with Docker (Production/Deployment)

To launch the entire application (including the database and web server) simultaneously:

```bash
docker-compose up --build
```
The application will automatically build the backend, launch the MySQL server, establish the network, and be available at `http://localhost:8000/`.
