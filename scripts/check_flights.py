#!/usr/bin/env python3
"""
Standalone script to check flight prices for all active search requests.
This script is designed to run as a scheduled job (e.g., via GitHub Actions).

Usage:
    python scripts/check_flights.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import get_all_active_search_requests, update_price_tracking_with_result
from app.serpapi_service import search_flights
from app.utils import get_cheapest_price_from_flight

def check_all_flights():
    """
    Check flight prices for all active search requests.
    Returns tuple: (success_count, failure_count, errors)
    """
    app = create_app()
    
    success_count = 0
    failure_count = 0
    errors = []
    
    with app.app_context():
        # Get all active search requests (future departure dates)
        print(f"[{datetime.now().isoformat()}] Fetching active search requests...")
        active_requests = get_all_active_search_requests()
        
        if not active_requests:
            print("No active search requests found.")
            return 0, 0, []
        
        print(f"Found {len(active_requests)} active search request(s).")
        print("-" * 80)
        
        # Process each request
        for idx, request in enumerate(active_requests, 1):
            request_id = request['id']
            depart_from = request['depart_from']
            arrive_at = request['arrive_at']
            departure_date = request['departure_date']
            
            print(f"\n[{idx}/{len(active_requests)}] Checking: {depart_from} -> {arrive_at} on {departure_date}")
            
            try:
                # Perform flight search
                search_result = search_flights(
                    depart_from=depart_from,
                    arrive_at=arrive_at,
                    departure_date=departure_date,
                    return_date=request.get('return_date'),
                    preferred_airlines=request.get('preferred_airlines'),
                    stops=request.get('stops', 0)
                )
                
                if search_result and search_result.get('success'):
                    cheapest_flight = search_result.get('cheapest_flight')
                    price = get_cheapest_price_from_flight(cheapest_flight)
                    
                    if price:
                        # Update price tracking with search result
                        update_price_tracking_with_result(
                            search_request_id=request_id,
                            price=price,
                            currency=cheapest_flight.get('currency', 'USD'),
                            airlines=cheapest_flight.get('airlines', []),
                            flight_details=cheapest_flight,
                            flight_link=cheapest_flight.get('link')
                        )
                        
                        currency = cheapest_flight.get('currency', 'USD')
                        print(f"  ✓ Success: Found cheapest flight at ${price:.2f} {currency}")
                        success_count += 1
                    else:
                        error_msg = "Flight search completed but no price found"
                        print(f"  ✗ Warning: {error_msg}")
                        errors.append({
                            'request_id': request_id,
                            'route': f"{depart_from} -> {arrive_at}",
                            'error': error_msg
                        })
                        failure_count += 1
                else:
                    error_msg = search_result.get('error', 'Unknown error') if search_result else 'No response from API'
                    print(f"  ✗ Failed: {error_msg}")
                    errors.append({
                        'request_id': request_id,
                        'route': f"{depart_from} -> {arrive_at}",
                        'error': error_msg
                    })
                    failure_count += 1
                    
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                print(f"  ✗ Error: {error_msg}")
                errors.append({
                    'request_id': request_id,
                    'route': f"{depart_from} -> {arrive_at}",
                    'error': error_msg
                })
                failure_count += 1
    
    return success_count, failure_count, errors

def main():
    """Main entry point for the script"""
    print("=" * 80)
    print("Flight Price Check Automation")
    print(f"Started at: {datetime.now().isoformat()}")
    print("=" * 80)
    
    try:
        success_count, failure_count, errors = check_all_flights()
        
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"Successful checks: {success_count}")
        print(f"Failed checks: {failure_count}")
        
        if errors:
            print("\nErrors encountered:")
            for error in errors:
                print(f"  - {error['route']}: {error['error']}")
        
        print(f"\nCompleted at: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Exit with non-zero code if there were failures
        # This helps GitHub Actions detect issues
        if failure_count > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
