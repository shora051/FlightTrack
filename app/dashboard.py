from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.forms import SearchRequestForm
from app.database import (
    create_search_request, get_user_search_requests, get_search_request_by_id,
    update_search_request, delete_search_request, get_price_tracking
)
from app.auth import login_required
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Display dashboard with user's search requests and create form"""
    user_id = session['user_id']
    
    # Get all search requests for the user
    requests = get_user_search_requests(user_id)
    
    # Get price tracking for each request
    requests_with_prices = []
    for req in requests:
        price_tracking = get_price_tracking(req['id'])
        req['price_tracking'] = price_tracking
        requests_with_prices.append(req)
    
    # Create form for new requests
    form = SearchRequestForm()
    
    return render_template('dashboard.html', 
                         requests=requests_with_prices, 
                         form=form)

@dashboard_bp.route('/create', methods=['POST'])
@login_required
def create():
    """Create a new search request"""
    user_id = session['user_id']
    form = SearchRequestForm()
    
    if form.validate_on_submit():
        # Prepare data
        return_date = None
        if form.trip_type.data == 'round_trip' and form.return_date.data:
            return_date = form.return_date.data.isoformat()
        
        preferred_airlines = form.preferred_airlines.data if form.preferred_airlines.data else None
        
        # Create search request
        search_request = create_search_request(
            user_id=user_id,
            depart_from=form.depart_from.data.strip(),
            arrive_at=form.arrive_at.data.strip(),
            departure_date=form.departure_date.data.isoformat(),
            return_date=return_date,
            passengers=form.passengers.data,
            trip_type=form.trip_type.data,
            preferred_airlines=preferred_airlines
        )
        
        if search_request:
            flash('Search request created successfully!', 'success')
        else:
            flash('An error occurred while creating the request.', 'danger')
    else:
        # Form validation failed
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
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
        # Prepare update data
        update_data = {
            'depart_from': form.depart_from.data.strip(),
            'arrive_at': form.arrive_at.data.strip(),
            'departure_date': form.departure_date.data.isoformat(),
            'passengers': form.passengers.data,
            'trip_type': form.trip_type.data,
            'preferred_airlines': form.preferred_airlines.data if form.preferred_airlines.data else None
        }
        
        # Handle return_date
        if form.trip_type.data == 'round_trip' and form.return_date.data:
            update_data['return_date'] = form.return_date.data.isoformat()
        else:
            update_data['return_date'] = None
        
        # Update the request
        updated = update_search_request(request_id, user_id, **update_data)
        
        if updated:
            flash('Search request updated successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('An error occurred while updating the request.', 'danger')
    else:
        # Pre-populate form with existing data
        form.depart_from.data = search_request['depart_from']
        form.arrive_at.data = search_request['arrive_at']
        form.departure_date.data = datetime.fromisoformat(search_request['departure_date']).date()
        if search_request.get('return_date'):
            form.return_date.data = datetime.fromisoformat(search_request['return_date']).date()
        form.passengers.data = search_request['passengers']
        form.trip_type.data = search_request['trip_type']
        if search_request.get('preferred_airlines'):
            form.preferred_airlines.data = search_request['preferred_airlines']
    
    return render_template('edit_request.html', form=form, request_id=request_id)

@dashboard_bp.route('/delete/<request_id>', methods=['POST'])
@login_required
def delete(request_id):
    """Delete a search request"""
    user_id = session['user_id']
    
    # Verify ownership and delete
    success = delete_search_request(request_id, user_id)
    
    if success:
        flash('Search request deleted successfully!', 'success')
    else:
        flash('Request not found or you do not have permission to delete it.', 'danger')
    
    return redirect(url_for('dashboard.index'))

