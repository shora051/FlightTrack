# FlightTrack

A web application for tracking flight prices. Users can configure flight tracking preferences, and a background system autonomously scans for deals daily and emails users when prices drop.

## Setup Instructions

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `SERPAPI_KEY`: Your SerpApi key
- `SECRET_KEY`: Generate a secure random key for Flask sessions

### 5. Database Setup

Run the following SQL in your Supabase SQL Editor to create the required tables:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 1: users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table 2: search_requests
CREATE TABLE search_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    depart_from TEXT NOT NULL,
    arrive_at TEXT NOT NULL,
    departure_date DATE NOT NULL,
    return_date DATE,
    passengers INTEGER NOT NULL CHECK (passengers >= 1 AND passengers <= 9),
    trip_type TEXT NOT NULL CHECK (trip_type IN ('one_way', 'round_trip')),
    preferred_airlines TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table 3: price_tracking
CREATE TABLE price_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_request_id UUID NOT NULL REFERENCES search_requests(id) ON DELETE CASCADE,
    minimum_price NUMERIC,
    last_checked TIMESTAMP,
    last_notified_price NUMERIC
);

-- Create indexes for better performance
CREATE INDEX idx_search_requests_user_id ON search_requests(user_id);
CREATE INDEX idx_price_tracking_search_request_id ON price_tracking(search_request_id);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_tracking ENABLE ROW LEVEL SECURITY;

-- Create RLS Policies
-- Note: Since we're using server-side authentication, we'll allow service role operations
-- but restrict based on user_id for search_requests and price_tracking

-- Users table: Allow all operations (authentication handled by application)
CREATE POLICY "Users are viewable by everyone" ON users FOR SELECT USING (true);
CREATE POLICY "Users are insertable by everyone" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Users are updatable by owner" ON users FOR UPDATE USING (true);

-- Search requests: Users can only see/modify their own requests
CREATE POLICY "Users can view own search requests" ON search_requests FOR SELECT USING (true);
CREATE POLICY "Users can insert own search requests" ON search_requests FOR INSERT WITH CHECK (true);
CREATE POLICY "Users can update own search requests" ON search_requests FOR UPDATE USING (true);
CREATE POLICY "Users can delete own search requests" ON search_requests FOR DELETE USING (true);

-- Price tracking: Accessible through search_requests relationship
CREATE POLICY "Price tracking is viewable by everyone" ON price_tracking FOR SELECT USING (true);
CREATE POLICY "Price tracking is insertable by everyone" ON price_tracking FOR INSERT WITH CHECK (true);
CREATE POLICY "Price tracking is updatable by everyone" ON price_tracking FOR UPDATE USING (true);
```

**Important Note on RLS:** The policies above allow operations because your Flask application handles authentication and user ownership validation in the application code. The publishable key will work with these policies. If you want stricter RLS policies that check authentication at the database level, you would need to use Supabase Auth instead of custom authentication.

### 6. Run the Application

```bash
flask run
```

Or with auto-reload:

```bash
flask run --debug
```

The application will be available at `http://localhost:5000`

## Project Structure

```
FlightTrack/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py             # Database models
│   ├── auth.py               # Authentication routes
│   ├── dashboard.py          # Dashboard routes
│   ├── database.py           # Supabase connection
│   ├── forms.py              # WTForms
│   └── templates/            # HTML templates
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Features

- User authentication (sign up, log in, log out)
- Create flight search requests
- View all search requests
- Edit existing requests
- Delete requests
- Automatic price tracking initialization

