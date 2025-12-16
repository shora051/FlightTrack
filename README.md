## FlightTrack

A web application for tracking flight prices. Users configure flight tracking preferences, and a background system checks for deals and emails users when prices drop.

---

## Setup Instructions

### 1. Create virtual environment

```bash
python -m venv venv
```

### 2. Activate virtual environment

**Windows (PowerShell):**

```bash
venv\Scripts\Activate
```

**macOS / Linux (bash/zsh):**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root with at least the following values:

```bash
# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_or_service_key

# SerpApi
SERPAPI_KEY=your_serpapi_key

# Flask
SECRET_KEY=a_secure_random_string

# Email (Gmail)
GMAIL_USER=your_gmail_address
GMAIL_APP_PASSWORD=your_gmail_app_password
```

- **`GMAIL_USER` / `GMAIL_APP_PASSWORD`** must correspond to a Gmail account with 2FA enabled and an App Password generated in **Google Account → Security → App passwords**.
- `GMAIL_FROM_EMAIL` defaults to `GMAIL_USER` if not set.

### 5. Database setup (Supabase)

The app uses Supabase with a simple three-table schema. In the **Supabase SQL editor**, run this once in your database:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Search requests configured by each user
CREATE TABLE IF NOT EXISTS public.search_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    depart_from TEXT NOT NULL,
    arrive_at TEXT NOT NULL,
    departure_date DATE NOT NULL,
    return_date DATE,
    trip_type TEXT NOT NULL CHECK (trip_type IN ('one_way', 'round_trip')),
    preferred_airlines TEXT[],
    stops INTEGER NOT NULL DEFAULT 0 CHECK (stops >= 0 AND stops <= 3),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Price tracking + latest result snapshot for each search request
CREATE TABLE IF NOT EXISTS public.price_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_request_id UUID NOT NULL REFERENCES public.search_requests(id) ON DELETE CASCADE,
    minimum_price NUMERIC,
    last_checked TIMESTAMPTZ,
    last_notified_price NUMERIC,
    latest_price NUMERIC,
    currency TEXT DEFAULT 'USD',
    airlines TEXT[],
    flight_details JSONB,
    flight_link TEXT
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_search_requests_user_id
    ON public.search_requests(user_id);

CREATE INDEX IF NOT EXISTS idx_price_tracking_search_request_id
    ON public.price_tracking(search_request_id);
```

This is all you need for a fresh setup. Any older migration/RLS complexity has been removed from the default instructions.

### 6. Run the application

From the project root, with your virtual environment active and `.env` configured:

```bash
python run.py
```

The app will start in debug mode and be available at `http://localhost:5000`.

If you prefer using the Flask CLI, you can instead set `FLASK_APP=run.py` and run:

```bash
flask run
```

---

## Project structure

```bash
FlightTrack/
├── app/
│   ├── __init__.py       # Flask app factory and config
│   ├── auth.py           # Authentication routes (signup/login)
│   ├── dashboard.py      # Dashboard and search request management
│   ├── database.py       # Supabase client helpers and CRUD
│   ├── models.py         # Simple Python models for DB rows
│   ├── forms.py          # WTForms definitions
│   ├── serpapi_service.py# SerpApi integration and result parsing
│   ├── email_service.py  # Email sending helpers
│   └── templates/        # HTML templates
├── scripts/
│   └── check_flights.py  # Script for scheduled/daily flight checks
├── .github/
│   └── workflows/
│       └── daily-flight-check.yml  # Example GitHub Actions workflow
├── requirements.txt
├── run.py
└── README.md
```

---

## Database schema overview

The live schema used by the application is:

- **`users`**: Stores user accounts
  - `id` (UUID, primary key)
  - `email` (unique)
  - `password_hash`
  - `created_at`

- **`search_requests`**: Stores each flight search configuration
  - `id` (UUID, primary key)
  - `user_id` (FK → `users.id`, cascade on delete)
  - `depart_from`, `arrive_at` (airport codes)
  - `departure_date`, `return_date` (optional)
  - `trip_type` (`one_way` or `round_trip`)
  - `preferred_airlines` (TEXT[])
  - `stops` (integer preference: 0 any, 1 nonstop, 2 one stop or fewer, 3 two stops or fewer)
  - `created_at`

- **`price_tracking`**: Consolidates tracking state and latest search result
  - `id` (UUID, primary key)
  - `search_request_id` (FK → `search_requests.id`, cascade on delete)
  - `minimum_price` (best price seen so far)
  - `last_checked` (timestamp of last search)
  - `last_notified_price` (last price that triggered an email)
  - `latest_price`, `currency`, `airlines`, `flight_details` (JSON snapshot of last result)
  - `flight_link` (direct link to the cheapest flight from the last search)

This three-table design keeps the schema small while still letting the app show the latest deal and track historical best prices for every saved search.
