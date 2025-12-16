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
- `GMAIL_SMTP_SERVER` (optional): Gmail SMTP server, defaults to `smtp.gmail.com`
- `GMAIL_SMTP_PORT` (optional): SMTP port, defaults to `587`
- `GMAIL_USER`: Your Gmail address used to send emails
- `GMAIL_APP_PASSWORD`: The 16-character App Password generated in your Google Account
- `GMAIL_FROM_EMAIL` (optional): From address, defaults to `GMAIL_USER`

To create a Gmail App Password:
1. Enable 2-Step Verification for your Google account.
2. In your Google Account under **Security → App passwords**, create a new App Password for \"Mail\".
3. Use the generated 16-character password as `GMAIL_APP_PASSWORD` in your `.env`.

### 5. Database Setup

The application uses a simplified schema with three core tables:

- **`users`**: Stores user account information
- **`search_requests`**: Stores user flight search configurations
- **`price_tracking`**: Stores price tracking metadata and latest search results

#### Initial Setup

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
-- Consolidated table that tracks price metadata and stores latest search result details
CREATE TABLE price_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_request_id UUID NOT NULL REFERENCES search_requests(id) ON DELETE CASCADE,
    minimum_price NUMERIC,
    last_checked TIMESTAMP,
    last_notified_price NUMERIC,
    -- Latest search result fields (consolidated from flight_search_results)
    latest_price NUMERIC,
    currency TEXT DEFAULT 'USD',
    airlines TEXT[],
    flight_details JSONB
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

#### Migration: Removing Redundant Tables

If you have an existing database with redundant tables (`flight_search_results`, `price_history`, `user_searches`), run this migration script to consolidate and clean up:

**⚠️ IMPORTANT: Before running this migration:**
1. **Back up your database** (Supabase has automatic backups, but you may want to export data)
2. **Review your data** - Make sure you understand what data will be migrated
3. Run this in a **new SQL editor tab** in Supabase

```sql
-- Step 1: Add new columns to price_tracking if they don't exist
-- (This must be done BEFORE migrating data)
ALTER TABLE price_tracking 
ADD COLUMN IF NOT EXISTS latest_price NUMERIC,
ADD COLUMN IF NOT EXISTS currency TEXT DEFAULT 'USD',
ADD COLUMN IF NOT EXISTS airlines TEXT[],
ADD COLUMN IF NOT EXISTS flight_details JSONB;

-- Step 2: Migrate latest search results from flight_search_results to price_tracking
-- This preserves the most recent search result for each search_request
-- Only runs if flight_search_results table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'flight_search_results') THEN
        UPDATE price_tracking pt
        SET 
            latest_price = fsr.price,
            currency = COALESCE(fsr.currency, 'USD'),
            airlines = fsr.airlines,
            flight_details = fsr.flight_details
        FROM (
            SELECT DISTINCT ON (search_request_id) 
                search_request_id,
                price,
                currency,
                airlines,
                flight_details
            FROM flight_search_results
            ORDER BY search_request_id, searched_at DESC
        ) fsr
        WHERE pt.search_request_id = fsr.search_request_id;
    END IF;
END $$;

-- Step 3: Drop redundant tables (after migration is complete)
-- WARNING: This will permanently delete data from these tables
-- Make sure you've migrated any important data first
DROP TABLE IF EXISTS flight_search_results CASCADE;
DROP TABLE IF EXISTS price_history CASCADE;
DROP TABLE IF EXISTS user_searches CASCADE;
```

### 7. Migration: Add flight link to price_tracking

Add a dedicated column for the outbound URL of the cheapest flight returned by SerpApi. This preserves the link even if the raw flight_details JSON changes.

```sql
ALTER TABLE price_tracking
ADD COLUMN IF NOT EXISTS flight_link TEXT;
```

**Warning:** The migration script above will delete the `flight_search_results`, `price_history`, and `user_searches` tables. Make sure you've reviewed and migrated any important data before running it.

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
- Create flight search requests with preferences (airlines, dates, passengers)
- View all search requests in a dashboard
- Edit existing requests
- Delete requests
- Automatic price tracking initialization
- Search for cheapest flights using SerpAPI Google Flights API
- Consolidated price tracking with latest search results
- Track minimum prices seen over time

## Database Schema

The application uses a simplified three-table schema:

1. **`users`**: Stores user account information (email, password hash)
2. **`search_requests`**: Stores user flight search configurations (route, dates, passengers, preferred airlines)
3. **`price_tracking`**: Consolidated table that tracks:
   - Minimum price seen (`minimum_price`)
   - Latest search result details (`latest_price`, `currency`, `airlines`, `flight_details`)
   - Tracking metadata (`last_checked`, `last_notified_price`)

This consolidated approach eliminates redundancy while maintaining all necessary functionality for price tracking.

