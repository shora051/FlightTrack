# Automated Flight Price Checking Setup Guide

This guide explains how to set up automated daily flight price checking using GitHub Actions.

## Overview

The automation system runs daily at 12 PM US Central Time to:
1. Retrieve all active search requests (with future departure dates)
2. Check flight prices using SerpAPI for each request
3. Update the database with the cheapest flight data
4. Automatically update the user dashboard

## Prerequisites

- GitHub repository for your FlightTrack project
- GitHub account with access to repository settings
- All required API keys (Supabase, SerpAPI)

## Setup Steps

### 1. Configure GitHub Secrets

GitHub Actions requires environment variables to be stored as secrets. You need to add the following secrets to your repository:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each of the following:

#### Required Secrets

- **`SUPABASE_URL`**: Your Supabase project URL
  - Example: `https://xxxxx.supabase.co`
  
- **`SUPABASE_KEY`**: Your Supabase anon/service key
  - Found in Supabase Dashboard → Settings → API
  
- **`SERPAPI_KEY`**: Your SerpAPI key
  - Found in your SerpAPI account dashboard
  
- **`SECRET_KEY`**: Flask secret key (same as in your `.env` file)
  - Used for Flask app initialization
  - Generate a secure random key if you don't have one

### 2. Verify Workflow File

The workflow file is located at:
```
.github/workflows/daily-flight-check.yml
```

This file is already configured to:
- Run daily at 12 PM US Central Time (17:00 UTC)
- Use Python 3.11
- Install dependencies from `requirements.txt`
- Run the `scripts/check_flights.py` script

### 3. Test Locally (Optional but Recommended)

Before relying on GitHub Actions, test the script locally:

```bash
# Make sure you're in the project root directory
# Ensure your .env file is configured with all required keys

# Run the script
python scripts/check_flights.py
```

Expected output:
- List of active search requests
- Flight search results for each request
- Summary of successful/failed checks

### 4. Test GitHub Actions Workflow

#### Manual Trigger

1. Go to your GitHub repository
2. Navigate to **Actions** tab
3. Select **Daily Flight Price Check** workflow
4. Click **Run workflow** → **Run workflow** (green button)
5. Monitor the workflow execution

#### Verify Scheduled Run

After the first manual run succeeds:
- The workflow will automatically run daily at 12 PM CT (17:00 UTC)
- Check the **Actions** tab to see scheduled runs
- Each run will show logs and execution status

## How It Works

### Workflow Execution Flow

```
GitHub Actions Scheduler (12 PM CT)
    ↓
Checkout repository code
    ↓
Set up Python environment
    ↓
Install dependencies
    ↓
Run check_flights.py script
    ↓
Script fetches active search requests
    ↓
For each request:
    - Calls SerpAPI to search flights
    - Updates database with cheapest price
    ↓
Dashboard automatically shows updated data
```

### Script Behavior

The `scripts/check_flights.py` script:

1. **Fetches Active Requests**: Gets all search requests where `departure_date >= today`
2. **Processes Each Request**: 
   - Calls SerpAPI flight search
   - Extracts cheapest flight price
   - Updates `price_tracking` table
3. **Error Handling**: 
   - Individual request failures don't stop the entire job
   - Errors are logged and reported in summary
4. **Summary Output**: Provides success/failure counts and error details

## Monitoring

### Check Workflow Status

1. Go to **Actions** tab in GitHub
2. View recent workflow runs
3. Click on a run to see detailed logs

### Check Database Updates

1. Log into your FlightTrack dashboard
2. View your search requests
3. Check the "Last Search" timestamp
4. Verify "Cheapest Price" is updated

### Common Issues

#### Workflow Fails with "Secret not found"

- **Solution**: Ensure all required secrets are configured in GitHub repository settings

#### Workflow Fails with "Module not found"

- **Solution**: Verify `requirements.txt` includes all dependencies
- Check that the script path is correct: `python scripts/check_flights.py`

#### No Active Requests Found

- **Solution**: This is normal if you don't have any search requests with future departure dates
- Create a test search request with a future date to verify the workflow

#### API Errors

- **Solution**: Check your API keys are correct and have sufficient quota
- Verify SerpAPI key is valid and not expired
- Check Supabase connection is working

## Timezone Configuration

The workflow is configured to run at **17:00 UTC**, which corresponds to:
- **12:00 PM Central Standard Time (CST)** - November to March
- **1:00 PM Central Daylight Time (CDT)** - March to November

To adjust the schedule, edit `.github/workflows/daily-flight-check.yml`:

```yaml
schedule:
  - cron: '0 17 * * *'  # Change 17 to desired UTC hour
```

Cron format: `minute hour day month day-of-week`
- `0 17 * * *` = Every day at 17:00 UTC

## Troubleshooting

### View Detailed Logs

1. Go to **Actions** → Select a workflow run
2. Click on **check-flights** job
3. Expand individual steps to see detailed output

### Test Script Manually

If the workflow fails, test the script locally:

```bash
# Set environment variables (or use .env file)
export SUPABASE_URL="your-url"
export SUPABASE_KEY="your-key"
export SERPAPI_KEY="your-key"
export SECRET_KEY="your-secret"

# Run script
python scripts/check_flights.py
```

### Verify Database Function

The script uses `get_all_active_search_requests()` from `app/database.py`. This function:
- Returns all search requests with `departure_date >= today`
- Orders by departure date (ascending)

## Security Notes

- **Never commit secrets**: All sensitive keys are stored as GitHub Secrets
- **Repository visibility**: If using a public repository, ensure secrets are properly configured
- **API key rotation**: Update GitHub Secrets if you rotate your API keys

## Next Steps

After setup:

1. ✅ Verify workflow runs successfully (manual trigger)
2. ✅ Check database updates after first run
3. ✅ Monitor scheduled runs for a few days
4. ✅ Set up notifications (optional) if you want email alerts on failures

## Support

If you encounter issues:
1. Check workflow logs in GitHub Actions
2. Test the script locally with your `.env` file
3. Verify all secrets are correctly configured
4. Ensure your database has active search requests with future dates
