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
from app.database import (
    get_all_active_search_requests,
    update_price_tracking_with_result,
    get_price_tracking,
    get_user_by_id,
    mark_price_notified,
)
from app.serpapi_service import search_flights
from app.utils import get_cheapest_price_from_flight, should_send_price_alert
from app.email_service import send_price_drop_email

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
                        # Get OLD tracking data BEFORE updating (to compare against previous minimum)
                        old_tracking = get_price_tracking(request_id)
                        old_minimum_price = old_tracking.get('minimum_price') if old_tracking else None
                        old_last_notified_price = old_tracking.get('last_notified_price') if old_tracking else None
                        
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

                        # After updating tracking, decide if we should send a price-drop alert
                        # Use OLD minimum_price for comparison (before it was updated to the new lower price)
                        try:
                            tracking = get_price_tracking(request_id)
                            user = get_user_by_id(request.get('user_id')) if request.get('user_id') else None

                            if tracking and user:
                                latest_price = tracking.get('latest_price')
                                # Use old_minimum_price for comparison, not the newly updated one
                                minimum_price = old_minimum_price
                                last_notified_price = old_last_notified_price

                                # Debug logging
                                old_min_str = f"${minimum_price:.2f}" if minimum_price is not None else "None"
                                last_notified_str = f"${last_notified_price:.2f}" if last_notified_price is not None else "None"
                                print(f"  → Price alert check: latest=${latest_price:.2f}, old_minimum={old_min_str}, last_notified={last_notified_str}")

                                if should_send_price_alert(latest_price, minimum_price, last_notified_price):
                                    print(f"  ✓ Price alert should be sent!")
                                    to_email = user.get('email')
                                    if to_email:
                                        dry_run_env = os.getenv("PRICE_ALERT_DRY_RUN", "false")
                                        dry_run = dry_run_env.lower().strip() in (
                                            "1",
                                            "true",
                                            "yes",
                                        )
                                        print(f"  → PRICE_ALERT_DRY_RUN env var: '{dry_run_env}' → dry_run={dry_run}")

                                        flight_link = tracking.get('flight_link')
                                        baseline = last_notified_price if last_notified_price is not None else minimum_price
                                        subject = "Cheaper flight found for your tracked route"
                                        html_body = f"""
                                        <html>
                                            <body>
                                                <p>Good news!</p>
                                                <p>We found a cheaper flight for your tracked route
                                                {depart_from} → {arrive_at} on {departure_date}.</p>
                                                <p>
                                                    Latest price: <strong>${float(latest_price):.2f} {currency}</strong><br/>
                                                    Previous best: <strong>${float(baseline):.2f} {currency}</strong>
                                                </p>
                                                {'<p><a href="' + flight_link + '">Book this flight</a></p>' if flight_link else ''}
                                                <p>Prices can change at any time, so if this works for you, consider booking soon.</p>
                                            </body>
                                        </html>
                                        """

                                        print(f"  → Sending price alert email to {to_email} (dry_run={dry_run})")
                                        email_sent = send_price_drop_email(
                                            to_email=to_email,
                                            subject=subject,
                                            html_body=html_body,
                                            dry_run=dry_run,
                                        )

                                        if email_sent and not dry_run:
                                            result = mark_price_notified(request_id, latest_price)
                                            if result:
                                                print(f"  ✓ Price alert notification recorded in database (last_notified_price=${latest_price:.2f})")
                                            else:
                                                print(f"  ✗ WARNING: Failed to update last_notified_price in database")
                                        elif dry_run:
                                            print(f"  → DRY RUN: Would mark last_notified_price=${latest_price:.2f} (email not actually sent)")
                                        elif not email_sent:
                                            print(f"  ✗ WARNING: Failed to send price alert email to {to_email} - last_notified_price NOT updated")
                                    else:
                                        print("  ✗ Skipping alert: user has no email on file.")
                                else:
                                    # Log why alert wasn't sent for debugging
                                    if latest_price is None:
                                        print(f"  → No alert: latest_price is None")
                                    elif minimum_price is None and last_notified_price is None:
                                        print(f"  → No alert: No baseline price available (minimum_price={minimum_price}, last_notified_price={last_notified_price})")
                                    else:
                                        baseline = last_notified_price if last_notified_price is not None else minimum_price
                                        if latest_price >= baseline:
                                            print(f"  → No alert: Latest price ${latest_price:.2f} is not lower than baseline ${baseline:.2f}")
                        except Exception as alert_error:
                            print(f"  Warning: error while processing price-drop alert logic: {alert_error}")
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
