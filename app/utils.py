"""
Utility functions and helpers for the application
"""
from typing import Optional, Dict, Any
from datetime import datetime
from flask import flash

def format_flash_errors(form_errors: Dict, form=None) -> None:
    """
    Format and flash form validation errors
    
    Args:
        form_errors: Dictionary of form field errors from WTForms
        form: Optional form instance to get field labels
    """
    for field, errors in form_errors.items():
        for error in errors:
            if form and hasattr(form, field):
                field_label = getattr(form, field).label.text
                flash(f'{field_label}: {error}', 'danger')
            else:
                flash(f'{field}: {error}', 'danger')

def prepare_search_request_data(form_data: Dict) -> Dict[str, Any]:
    """
    Prepare search request data from form submission
    
    Args:
        form_data: Dictionary containing form data
    
    Returns:
        Dictionary with prepared search request data
    """
    return_date = None
    if form_data.get('trip_type') == 'round_trip' and form_data.get('return_date'):
        return_date = form_data['return_date'].isoformat() if hasattr(form_data['return_date'], 'isoformat') else form_data['return_date']
    
    return {
        'depart_from': form_data['depart_from'].strip() if isinstance(form_data.get('depart_from'), str) else form_data.get('depart_from'),
        'arrive_at': form_data['arrive_at'].strip() if isinstance(form_data.get('arrive_at'), str) else form_data.get('arrive_at'),
        'departure_date': form_data['departure_date'].isoformat() if hasattr(form_data.get('departure_date'), 'isoformat') else form_data.get('departure_date'),
        'return_date': return_date,
        'passengers': form_data.get('passengers'),
        'trip_type': form_data.get('trip_type'),
        'preferred_airlines': form_data.get('preferred_airlines') if form_data.get('preferred_airlines') else None,
        'stops': form_data.get('stops', 0)
    }

def populate_form_from_search_request(form, search_request: Dict) -> None:
    """
    Populate a form with data from a search request
    
    Args:
        form: WTForms form instance
        search_request: Dictionary containing search request data
    """
    form.depart_from.data = search_request.get('depart_from')
    form.arrive_at.data = search_request.get('arrive_at')
    form.departure_date.data = datetime.fromisoformat(search_request['departure_date']).date()
    if search_request.get('return_date'):
        form.return_date.data = datetime.fromisoformat(search_request['return_date']).date()
    form.passengers.data = search_request.get('passengers')
    form.trip_type.data = search_request.get('trip_type')
    form.stops.data = search_request.get('stops', 0)
    if search_request.get('preferred_airlines'):
        form.preferred_airlines.data = search_request['preferred_airlines']

def get_cheapest_price_from_flight(flight_data: Optional[Dict]) -> Optional[float]:
    """
    Extract price from flight data
    
    Args:
        flight_data: Flight data dictionary
    
    Returns:
        Price as float, or None if not found
    """
    if not flight_data:
        return None
    
    price_info = flight_data.get('price')
    if isinstance(price_info, dict):
        return float(price_info.get('total', 0)) if price_info.get('total') else None
    elif isinstance(price_info, (int, float)):
        return float(price_info)
    return None
