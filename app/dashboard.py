from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.forms import SearchRequestForm
from app.database import (
    create_search_request, get_user_search_requests_with_tracking, get_search_request_by_id,
    update_search_request, delete_search_request,
    update_price_tracking_with_result
)
from app.auth import login_required
from app.serpapi_service import search_flights
from app.utils import format_flash_errors, prepare_search_request_data, populate_form_from_search_request, get_cheapest_price_from_flight
from app.constants import FLASH_SUCCESS, FLASH_DANGER, FLASH_WARNING

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Display dashboard with user's search requests and create form"""
    user_id = session['user_id']
    
    # Get all search requests with tracking data (optimized single query)
    requests = get_user_search_requests_with_tracking(user_id)
    
    # Create form for new requests
    form = SearchRequestForm()
    
    return render_template('dashboard.html', 
                         requests=requests, 
                         form=form)

@dashboard_bp.route('/create', methods=['POST'])
@login_required
def create():
    """Create a new search request"""
    user_id = session['user_id']
    form = SearchRequestForm()
    
    if form.validate_on_submit():
        # Prepare data using utility function
        form_data = {
            'depart_from': form.depart_from.data,
            'arrive_at': form.arrive_at.data,
            'departure_date': form.departure_date.data,
            'return_date': form.return_date.data,
            'passengers': form.passengers.data,
            'trip_type': form.trip_type.data,
            'preferred_airlines': form.preferred_airlines.data,
            'stops': form.stops.data
        }
        request_data = prepare_search_request_data(form_data)
        
        # Create search request
        search_request = create_search_request(user_id=user_id, **request_data)
        
        if search_request:
            flash('Search request created successfully!', FLASH_SUCCESS)
        else:
            flash('An error occurred while creating the request.', FLASH_DANGER)
    else:
        format_flash_errors(form.errors, form)
    
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/edit/<request_id>', methods=['GET', 'POST'])
@login_required
def edit(request_id):
    """Edit an existing search request"""
    user_id = session['user_id']
    
    # Get the request and verify ownership
    search_request = get_search_request_by_id(request_id, user_id)
    
    if not search_request:
        flash('Request not found or you do not have permission to edit it.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = SearchRequestForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        # Prepare update data using utility function
        form_data = {
            'depart_from': form.depart_from.data,
            'arrive_at': form.arrive_at.data,
            'departure_date': form.departure_date.data,
            'return_date': form.return_date.data,
            'passengers': form.passengers.data,
            'trip_type': form.trip_type.data,
            'preferred_airlines': form.preferred_airlines.data,
            'stops': form.stops.data
        }
        update_data = prepare_search_request_data(form_data)
        
        # Update the request
        updated = update_search_request(request_id, user_id, **update_data)
        
        if updated:
            flash('Search request updated successfully!', FLASH_SUCCESS)
            return redirect(url_for('dashboard.index'))
        else:
            flash('An error occurred while updating the request.', FLASH_DANGER)
    else:
        # Pre-populate form with existing data using utility function
        populate_form_from_search_request(form, search_request)
    
    return render_template('edit_request.html', form=form, request_id=request_id)

@dashboard_bp.route('/delete/<request_id>', methods=['POST'])
@login_required
def delete(request_id):
    """Delete a search request"""
    user_id = session['user_id']
    
    # Verify ownership and delete
    success = delete_search_request(request_id, user_id)
    
    if success:
        flash('Search request deleted successfully!', FLASH_SUCCESS)
    else:
        flash('Request not found or you do not have permission to delete it.', FLASH_DANGER)
    
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/search/<request_id>', methods=['POST'])
@login_required
def search_flights_for_request(request_id):
    """Search for flights for a specific search request"""
    user_id = session['user_id']
    
    # Verify ownership
    search_request = get_search_request_by_id(request_id, user_id)
    if not search_request:
        flash('Request not found or you do not have permission to search it.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Perform flight search using SerpAPI
        search_result = search_flights(
            depart_from=search_request['depart_from'],
            arrive_at=search_request['arrive_at'],
            departure_date=search_request['departure_date'],
            return_date=search_request.get('return_date'),
            passengers=search_request['passengers'],
            preferred_airlines=search_request.get('preferred_airlines'),
            stops=search_request.get('stops', 0)
        )
        
        if search_result and search_result.get('success'):
            cheapest_flight = search_result.get('cheapest_flight')
            price = get_cheapest_price_from_flight(cheapest_flight)
            
            if price:
                # Update price tracking with search result (consolidated operation)
                update_price_tracking_with_result(
                    search_request_id=request_id,
                    price=price,
                    currency=cheapest_flight.get('currency', 'USD'),
                    airlines=cheapest_flight.get('airlines', []),
                    flight_details=cheapest_flight,
                    flight_link=cheapest_flight.get('link')
                )
                
                currency = cheapest_flight.get('currency', 'USD')
                flash(f'Flight search completed! Cheapest flight found: ${price:.2f} {currency}', FLASH_SUCCESS)
            else:
                flash('Flight search completed but no flights were found.', FLASH_WARNING)
        else:
            error_msg = search_result.get('error', 'Unknown error') if search_result else 'No response from API'
            flash(f'Flight search failed: {error_msg}', FLASH_DANGER)
    
    except Exception as e:
        print(f"Error searching flights: {e}")
        flash(f'An error occurred while searching for flights: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard.index'))

