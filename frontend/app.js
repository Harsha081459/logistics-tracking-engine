const API_URL = 'http://127.0.0.1:8000/api';

const app = {
    state: { currentCustomer: null },

    showView: (viewId) => {
        document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        const target = document.getElementById(viewId);
        target.classList.remove('hidden');
        target.classList.add('active');

        const navActions = document.getElementById('nav-actions');
        if (viewId === 'view-landing') {
            navActions.classList.add('hidden');
            app.state.currentCustomer = null;
        } else {
            navActions.classList.remove('hidden');
        }

        if (viewId === 'view-customer-dashboard') app.loadCustomerDashboard();
        else if (viewId === 'view-employee') app.loadEmployeeFlights();
    },

    switchAuthTab: (tab) => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.auth-form').forEach(f => f.classList.add('hidden'));
        if (tab === 'login') {
            document.querySelector('.tab:nth-child(1)').classList.add('active');
            document.getElementById('form-login').classList.remove('hidden');
        } else {
            document.querySelector('.tab:nth-child(2)').classList.add('active');
            document.getElementById('form-register').classList.remove('hidden');
        }
    },

    showToast: (message, isError = false) => {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.style.background = isError ? 'var(--danger)' : 'var(--primary)';
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3000);
    },

    // --- Public Tracking Timeline ---
    handlePublicTracking: async (e) => {
        e.preventDefault();
        const trackingId = document.getElementById('public-track-id').value;
        const resultContainer = document.getElementById('public-tracking-result');
        
        try {
            const res = await fetch(`${API_URL}/tracking/${trackingId}`);
            if (!res.ok) throw new Error("Tracking number not found");
            const data = await res.json();
            
            let html = `<h3>Package: ${data.cargo.TrackingNumber}</h3>
                        <p class="mb-4">Status: <span class="highlight">${data.cargo.CurrentStatus}</span></p>`;
            
            data.timeline.forEach((event, idx) => {
                html += `
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">${event.Timestamp}</div>
                    <div class="timeline-status">${event.Status}</div>
                    <div class="timeline-location">${event.Location}</div>
                    ${event.Remarks ? `<div class="timeline-remarks">"${event.Remarks}"</div>` : ''}
                </div>`;
            });
            
            resultContainer.innerHTML = html;
            resultContainer.classList.remove('hidden');
        } catch (err) {
            app.showToast(err.message, true);
            resultContainer.classList.add('hidden');
        }
    },

    // --- Auth ---
    handleCustomerLogin: async (e) => {
        e.preventDefault();
        const payload = {
            customer_id: document.getElementById('login-id').value,
            password: document.getElementById('login-password').value
        };
        try {
            const res = await fetch(`${API_URL}/auth/login`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
            });
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail);
            }
            const data = await res.json();
            
            // SAVE JWT TOKEN
            localStorage.setItem('jwt', data.access_token);
            app.state.currentCustomer = data.customer;
            document.getElementById('customer-name-display').textContent = data.customer.Name;
            
            app.showView('view-customer-dashboard');
            app.showToast('Login successful!');
        } catch (err) {
            app.showToast(err.message, true);
        }
    },

    handleCustomerRegister: async (e) => {
        e.preventDefault();
        const payload = {
            customer_id: document.getElementById('reg-id').value,
            name: document.getElementById('reg-name').value,
            email: document.getElementById('reg-email').value,
            phone: document.getElementById('reg-phone').value,
            address: document.getElementById('reg-address').value,
            password: document.getElementById('reg-password').value
        };
        try {
            const res = await fetch(`${API_URL}/auth/register`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error(await res.text());
            app.showToast('Registration successful! Please login.');
            app.switchAuthTab('login');
            document.getElementById('login-id').value = payload.customer_id;
        } catch (err) {
            let msg = 'Registration failed';
            try { msg = JSON.parse(err.message).detail; } catch (e) { msg = err.message; }
            app.showToast(`Error: ${msg}`, true);
        }
    },

    // --- Customer Dashboard ---
    loadCustomerDashboard: async () => {
        app.loadAvailableFlights('book-flight-id');
        app.loadCustomerBookings();
    },

    loadAvailableFlights: async (selectElementId) => {
        try {
            const res = await fetch(`${API_URL}/flights`);
            const flights = await res.json();
            const select = document.getElementById(selectElementId);
            select.innerHTML = '';
            flights.forEach(f => {
                select.innerHTML += `<option value="${f.FlightID}">${f.OriginHub} ✈️ ${f.DestinationHub} (${f.DepartureDate})</option>`;
            });
        } catch (err) {}
    },

    previewPrice: async () => {
        const weight = document.getElementById('book-weight').value;
        const type = document.getElementById('book-type').value;
        if (!weight) return;
        
        try {
            const res = await fetch(`${API_URL}/pricing`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ weight: parseFloat(weight), cargo_type: type })
            });
            const data = await res.json();
            document.getElementById('price-display').textContent = `$${data.total_cost.toFixed(2)}`;
        } catch (err) {}
    },

    loadCustomerBookings: async () => {
        const token = localStorage.getItem('jwt');
        if (!token) return;
        try {
            const res = await fetch(`${API_URL}/customers/me/bookings`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.status === 401) { app.showToast("Session expired", true); return; }
            const bookings = await res.json();
            const list = document.getElementById('customer-bookings-list');
            list.innerHTML = '';
            
            if (bookings.length === 0) {
                list.innerHTML = '<p class="text-muted">No active shipments found.</p>';
                return;
            }

            bookings.forEach(b => {
                list.innerHTML += `
                    <div class="item-card">
                        <div class="details">
                            <h4>Track: ${b.TrackingNumber}</h4>
                            <p>${b.OriginHub} ✈️ ${b.DestinationHub}</p>
                            <p>Cost: $${b.TotalCost.toFixed(2)}</p>
                        </div>
                        <div class="actions" style="text-align: right;">
                            <span class="badge ${b.CurrentStatus === 'Delivered' ? 'done' : 'active'}">${b.CurrentStatus}</span>
                        </div>
                    </div>
                `;
            });
        } catch (err) {}
    },

    handleBookCargo: async (e) => {
        e.preventDefault();
        const payload = {
            flight_id: document.getElementById('book-flight-id').value,
            cargo_id: document.getElementById('book-cargo-id').value || `CRG${Math.floor(Math.random()*10000)}`,
            weight: parseFloat(document.getElementById('book-weight').value),
            cargo_type: document.getElementById('book-type').value
        };

        const token = localStorage.getItem('jwt');
        try {
            const res = await fetch(`${API_URL}/customers/me/bookings`, {
                method: 'POST', 
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }, 
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error(await res.text());
            const data = await res.json();
            app.showToast(`Success! Tracking Number: ${data.details.TrackingNumber}`);
            e.target.reset();
            document.getElementById('price-display').textContent = '$0.00';
            app.loadCustomerDashboard();
        } catch (err) {
            app.showToast('Booking failed', true);
        }
    },

    // --- Employee Console ---
    loadEmployeeFlights: async () => {
        try {
            const res = await fetch(`${API_URL}/flights`);
            const flights = await res.json();
            const list = document.getElementById('employee-flights-list');
            list.innerHTML = '';
            flights.forEach(f => {
                list.innerHTML += `
                    <div class="item-card">
                        <div class="details">
                            <h4>Flight: ${f.FlightID}</h4>
                            <p>${f.OriginHub} ✈️ ${f.DestinationHub}</p>
                        </div>
                        <div class="actions">
                            <span class="badge active">${f.AvailableCapacity}kg Space</span>
                        </div>
                    </div>`;
            });
        } catch (err) {}
    },

    loadEmployeeTracking: async () => {
        const id = document.getElementById('emp-track-id').value;
        if (!id) return;
        try {
            const res = await fetch(`${API_URL}/tracking/${id}`);
            if (!res.ok) throw new Error("Not found");
            const data = await res.json();
            
            document.getElementById('emp-scan-title').textContent = `Tracking: ${data.cargo.TrackingNumber}`;
            document.getElementById('emp-scan-subtitle').textContent = `Current Status: ${data.cargo.CurrentStatus}`;
            document.getElementById('update-location').value = data.cargo.CurrentLocation;
            document.getElementById('emp-scan-result').classList.remove('hidden');
        } catch (err) {
            app.showToast('Invalid Tracking Barcode', true);
        }
    },

    updateTracking: async (e) => {
        e.preventDefault();
        const trackingId = document.getElementById('emp-track-id').value;
        const payload = {
            status: document.getElementById('update-status').value,
            location: document.getElementById('update-location').value,
            remarks: document.getElementById('update-remarks').value
        };
        try {
            const res = await fetch(`${API_URL}/tracking/${trackingId}/update`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error(await res.text());
            app.showToast('Timeline updated successfully!');
            document.getElementById('emp-scan-result').classList.add('hidden');
        } catch (err) {
            app.showToast('Update failed', true);
        }
    }
};

document.getElementById('logout-btn').addEventListener('click', () => {
    localStorage.removeItem('jwt');
    app.showView('view-landing');
    app.showToast('Logged out successfully');
});
