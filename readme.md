# Bike & Car Rental Platform — Complete Documentation

## Overview

**Bike & Car Rental** is a full-stack Django REST Framework application for managing vehicle rentals (cars and bikes). It includes user authentication, booking management, Stripe payment integration, and a Bootstrap-based frontend.

- **Backend**: Django 4.2 + Django REST Framework
- **Frontend**: Bootstrap 5 + Vanilla JavaScript
- **Database**: SQLite (local) / PostgreSQL (production)
- **Payments**: Stripe Checkout + Webhook verification
- **Deployment**: Render, Docker, or traditional servers

---

## Project Structure

```
project-root/
├── config/                    # Django project configuration
│   ├── settings.py           # Settings (database, auth, static files, Stripe)
│   ├── urls.py               # Main URL router
│   ├── wsgi.py               # WSGI entry point
│   └── asgi.py               # ASGI entry point
├── rentals/                   # Main Django app
│   ├── models.py             # Database models (Vehicle, Booking, Payment, Review)
│   ├── serializers.py        # DRF serializers for API responses
│   ├── views.py              # API views (ListCreateView, RetrieveUpdateView, etc.)
│   ├── frontend_views.py     # Frontend template views (render HTML pages)
│   ├── urls_updated.py       # API & frontend URL routing
│   ├── admin.py              # Django admin configuration
│   ├── utils.py              # Utility functions (availability checks)
│   ├── tests.py              # Unit tests
│   ├── migrations/           # Database migrations
│   └── templates/            # HTML templates (if app-level templates needed)
├── templates/                # Global HTML templates
│   ├── home.html             # Home page
│   ├── vehicles.html         # Vehicles list page
│   ├── vehicle_detail.html   # Vehicle detail + booking form
│   ├── payment.html          # Payment checkout page (Stripe)
│   ├── dashboard.html        # User dashboard (bookings, profile)
│   ├── login.html            # Login page
│   ├── register.html         # Sign-up page
│   └── navbar.html           # Shared navbar component
├── static/                   # Static assets (CSS, JS, images)
├── staticfiles/              # Collected static files for production
├── media/                    # User-uploaded files (vehicle images)
├── db.sqlite3               # SQLite database (local development)
├── manage.py                # Django CLI tool
├── requirements.txt         # Python dependencies
├── render.yaml              # Render deployment manifest
├── Procfile                 # Heroku/Render process definition
├── docker-compose.yml       # Docker Compose (optional local Postgres)
├── .env.example             # Environment variables template
└── README.md                # Setup & quick start guide
```

---

## Core Components

### 1. Database Models

#### `Vehicle`
Represents a car or bike available for rent.

```python
class Vehicle(models.Model):
    type              # 'car' or 'bike'
    title             # e.g. "2024 Tesla Model 3"
    description       # Detailed description
    make              # Manufacturer
    model             # Model name
    year              # Manufacturing year
    seats             # Number of seats
    price_per_day     # Daily rental rate (decimal)
    deposit           # Security deposit
    location_city     # City where vehicle is located
    is_active         # Availability status
    created_at        # Creation timestamp
```

#### `VehicleImage`
Photos for each vehicle (one-to-many relationship).

```python
class VehicleImage(models.Model):
    vehicle           # Foreign key to Vehicle
    image             # ImageField (upload_to='vehicles/')
    alt_text          # Accessibility alt text
```

#### `Booking`
Represents a rental reservation.

```python
class Booking(models.Model):
    user              # Foreign key to User
    vehicle           # Foreign key to Vehicle
    start_date        # Check-in date
    end_date          # Check-out date (inclusive)
    total_price       # Calculated rent + deposit
    status            # 'pending', 'confirmed', 'cancelled', 'completed'
    created_at        # Booking creation timestamp
```

**Availability Logic**: A vehicle is available if no existing bookings overlap:
```python
# Overlap check: start_date <= end_date AND end_date >= start_date
# (end_date is treated as inclusive)
if is_vehicle_available(vehicle, start_date, end_date):
    # Safe to book
```

#### `Payment`
Stripe payment record linked to a booking.

```python
class Payment(models.Model):
    booking           # OneToOne to Booking
    amount            # Total payment amount
    stripe_payment_intent  # Stripe intent ID
    paid              # Payment status (Boolean)
    paid_at           # Payment completion timestamp
```

#### `Review`
Customer reviews (optional).

```python
class Review(models.Model):
    booking           # OneToOne to Booking
    rating            # 1-5 stars
    comment           # Written feedback
    created_at        # Review timestamp
```

---

### 2. API Endpoints

All API endpoints return JSON when called with `?format=json` or `Accept: application/json` header.

#### Authentication
- **POST** `/api/auth/token/` — Get auth token (username + password)
- **POST** `/api/auth/register/` — Create new user account + return token
- **GET** `/api/auth/check-username/?username=...` — Check if username is available
- **GET/PUT** `/api/auth/user/` — View/update current user profile

#### Vehicles
- **GET** `/api/vehicles/?format=json` — List all vehicles (supports filters: `type`, `seats`, `min_price`, `max_price`, `city`)
- **GET** `/api/vehicles/{id}/?format=json` — Get vehicle details (includes images)

#### Bookings
- **POST** `/api/bookings/` — Create a new booking (requires auth)
- **GET** `/api/bookings/my/` — List user's bookings (requires auth)
- **GET** `/api/bookings/{id}/` — Get booking details (requires auth, owner only)
- **POST** `/api/bookings/{id}/cancel/` — Cancel a booking (requires auth, owner only)

#### Payments
- **POST** `/api/payments/create-checkout/` — Create Stripe Checkout session
  - Request: `{ "booking_id": 123 }`
  - Response: `{ "sessionId": "cs_test_..." }`
- **POST** `/api/webhooks/stripe/` — Stripe webhook receiver (updates booking status on payment)

---

### 3. Frontend Pages

#### Home (`/`)
- Hero section with CTA button
- Features overview
- Navbar with login/logout options

#### Vehicles List (`/vehicles/`)
- Grid of all available vehicles with images
- Search/filter by type, seats, price range, city
- "View & Book" buttons link to vehicle detail page

#### Vehicle Detail (`/vehicle/{id}/`)
- Full vehicle info with images
- Booking form (date picker for start/end dates)
- Price calculation: `(days * price_per_day) + deposit`
- "Book Now" submits to API, redirects to payment

#### Payment (`/payment/{booking_id}/`)
- Booking summary (vehicle, dates, price)
- Stripe card element (via Stripe.js)
- "Pay Now" button creates Stripe Checkout session
- Redirects to Stripe Checkout (hosted payment page)
- On success: booking status → `confirmed`, payment marked as paid

#### Dashboard (`/dashboard/`)
- **Profile Section**: View/edit email, first_name, last_name
- **Bookings Section**: List all user bookings with statuses
- **Cancel Button**: Cancel pending bookings
- **Logout Button**: Clear token and redirect to login

#### Login (`/login/`)
- Username + password form
- Submits to `/api/auth/token/`
- On success: stores token in `localStorage`, redirects to `/dashboard/`
- Auto-redirects if already logged in

#### Register (`/register/`)
- Username, email, password form
- Real-time username availability check (onblur)
- Submits to `/api/auth/register/`
- On success: auto-logs in and redirects to `/dashboard/`

---

## Key Features

### 1. User Authentication
- **Token-based auth** (DRF TokenAuthentication)
- Tokens stored in browser `localStorage`
- No session cookies by default (API-first design)
- Optional: Session auth also enabled for browsable API

### 2. Booking & Availability
- **Date overlap validation**: Prevents double-bookings
- **Inclusive end date**: Customer can keep vehicle until end of end_date
- **Auto-calculated price**: `(end_date - start_date + 1) * price_per_day + deposit`
- **Status tracking**: pending → confirmed (on payment) → completed

### 3. Stripe Integration
- **Checkout Sessions**: Server-side session creation for PCI compliance
- **Webhook verification**: Validates Stripe signatures using `STRIPE_WEBHOOK_SECRET`
- **Automatic confirmation**: Webhook updates booking status to `confirmed` on `checkout.session.completed` event
- **Test mode**: Use test Stripe keys from https://dashboard.stripe.com/keys

### 4. Vehicle Images
- **Multiple images per vehicle** (one-to-many)
- **API serialization**: VehicleSerializer includes `images` array
- **Frontend display**: Falls back to placeholder if image missing/fails to load

### 5. Admin Management
- Django admin interface at `/admin/`
- Add/edit vehicles, bookings, payments, reviews
- Bulk actions (mark as active/inactive, etc.)

---

## Environment Variables

Create a `.env` file in the project root:

```bash
# Django
SECRET_KEY=your-secure-random-key-here
DEBUG=False                           # Set to True for local development
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database
DATABASE_URL=sqlite:///db.sqlite3    # Local: SQLite
# DATABASE_URL=postgres://user:pass@host:5432/dbname  # Production: Postgres

# Stripe
STRIPE_SECRET_KEY=sk_test_...        # Get from Stripe Dashboard
STRIPE_PUBLISHABLE_KEY=pk_test_...   # Publishable key for frontend
STRIPE_WEBHOOK_SECRET=whsec_...      # Set after configuring webhook

# Optional
REDIS_URL=redis://localhost:6379/0   # For caching/celery (not yet used)
```

---

## Installation & Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/sumanm202/bike-rental.git
   cd bike-rental
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file** (see Environment Variables section above)

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Collect static files**
   ```bash
   python manage.py collectstatic --noinput
   ```

7. **Create superuser** (for admin panel)
   ```bash
   python manage.py createsuperuser
   ```

8. **Start dev server**
   ```bash
   python manage.py runserver
   ```
   Visit: http://127.0.0.1:8000

---

## Running Tests

```bash
python manage.py test
```

Tests include:
- Availability overlap validation
- Booking creation & cancellation
- Payment webhook processing
- API endpoint access control

---

## File Reference

| File | Purpose |
|------|---------|
| `config/settings.py` | Django settings, DB config, middleware, static files |
| `rentals/models.py` | Database schema (Vehicle, Booking, Payment, etc.) |
| `rentals/serializers.py` | DRF serializers for API JSON responses |
| `rentals/views.py` | API views (ListCreateView, Stripe webhook handler) |
| `rentals/frontend_views.py` | Frontend views (render HTML templates) |
| `rentals/urls_updated.py` | URL routing (API + frontend endpoints) |
| `rentals/utils.py` | Utility functions (availability checks) |
| `rentals/admin.py` | Django admin site configuration |
| `rentals/tests.py` | Unit tests |
| `templates/*.html` | Bootstrap templates (home, vehicles, payment, etc.) |
| `requirements.txt` | Python package dependencies |
| `render.yaml` | Render deployment manifest |
| `Procfile` | App startup command |
| `.env.example` | Environment variable template |

---
