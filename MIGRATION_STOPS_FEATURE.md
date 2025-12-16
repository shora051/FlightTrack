# Migration Guide: Adding Stops Feature

## Summary
This migration adds the "Number of Stops" option to the FlightTrack dashboard, allowing users to filter flights by the number of stops they prefer.

## Changes Made

### 1. Database Schema
- **File**: `migrations/add_stops_column.sql`
- Added `stops` column to `search_requests` table
- Column type: INTEGER with CHECK constraint (0-3)
- Default value: 0 (Any number of stops)

### 2. Form Updates
- **File**: `app/forms.py`
- Added `stops` field to `SearchRequestForm` with options:
  - 0: Any number of stops (default)
  - 1: Nonstop only
  - 2: 1 stop or fewer
  - 3: 2 stops or fewer

### 3. Model Updates
- **File**: `app/models.py`
- Updated `SearchRequest` model to include `stops` field
- Updated `from_dict()` and `to_dict()` methods

### 4. Database Functions
- **File**: `app/database.py`
- Updated `create_search_request()` to accept and store `stops` parameter

### 5. Utility Functions
- **File**: `app/utils.py`
- Updated `prepare_search_request_data()` to include `stops` in form data
- Updated `populate_form_from_search_request()` to populate `stops` field

### 6. API Integration
- **File**: `app/serpapi_service.py`
- Updated `search_flights()` to accept `stops` parameter
- Added logic to pass `stops` to SerpAPI (only when stops > 0, as 0 is the default)

### 7. Dashboard Updates
- **File**: `app/dashboard.py`
- Updated `create()` route to handle `stops` in form submission
- Updated `edit()` route to handle `stops` in form updates
- Updated `search_flights_for_request()` to pass `stops` to API

### 8. Template Updates
- **Files**: 
  - `app/templates/dashboard.html`
  - `app/templates/edit_request.html`
- Added `stops` field to create and edit forms
- Added "Stops" column to the requests table display
- Added visual badges to show stops preference

## Next Steps

### 1. Run Database Migration
Execute the SQL migration in your Supabase SQL Editor:

```sql
-- Run the contents of migrations/add_stops_column.sql
ALTER TABLE search_requests 
ADD COLUMN IF NOT EXISTS stops INTEGER DEFAULT 0 CHECK (stops >= 0 AND stops <= 3);

UPDATE search_requests SET stops = 0 WHERE stops IS NULL;
```

### 2. Test the Feature
1. Create a new search request with different stops options
2. Edit an existing search request and change the stops preference
3. Perform a flight search and verify the stops parameter is passed to the API
4. Check that existing requests default to "Any stops" (0)

### 3. Verify API Integration
- Check that the `stops` parameter is correctly sent to SerpAPI
- Verify that flight search results respect the stops preference

## Notes
- Existing search requests will default to `stops = 0` (Any number of stops)
- The stops parameter is only sent to SerpAPI when `stops > 0` (to avoid unnecessary parameters)
- The feature is backward compatible - existing code will work with the default value of 0

