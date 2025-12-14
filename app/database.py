from supabase import create_client, Client
from flask import current_app
from typing import Optional, Dict, List

# Module-level cache for Supabase client (per application context)
_supabase_client = None

def get_supabase_client() -> Client:
    """Get Supabase client instance (cached per application context)"""
    global _supabase_client
    
    # Return cached client if available
    if _supabase_client is not None:
        return _supabase_client
    
    url = current_app.config.get('SUPABASE_URL')
    key = current_app.config.get('SUPABASE_KEY')
    
    if not url or not key:
        raise ValueError("Supabase URL and Key must be set in environment variables")
    
    # Strip any whitespace from the key and URL
    url = url.strip()
    key = key.strip()
    
    try:
        _supabase_client = create_client(url, key)
        return _supabase_client
    except Exception as e:
        # Provide more detailed error information
        error_type = type(e).__name__
        error_msg = str(e)
        raise ValueError(
            f"Failed to create Supabase client: {error_type}: {error_msg}. "
            f"URL length: {len(url) if url else 0}, Key length: {len(key) if key else 0}. "
            f"Please verify your SUPABASE_URL and SUPABASE_KEY in .env file."
        ) from e

def create_user(email: str, password_hash: str) -> Optional[Dict]:
    """Create a new user in the database"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('users').insert({
            'email': email,
            'password_hash': password_hash
        }).execute()
        
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('users').select('*').eq('email', email).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def create_search_request(user_id: str, depart_from: str, arrive_at: str, 
                         departure_date: str, return_date: Optional[str],
                         passengers: int, trip_type: str, 
                         preferred_airlines: Optional[List[str]]) -> Optional[Dict]:
    """Create a new search request"""
    supabase = get_supabase_client()
    try:
        data = {
            'user_id': user_id,
            'depart_from': depart_from,
            'arrive_at': arrive_at,
            'departure_date': departure_date,
            'return_date': return_date,
            'passengers': passengers,
            'trip_type': trip_type,
            'preferred_airlines': preferred_airlines
        }
        
        result = supabase.table('search_requests').insert(data).execute()
        
        if result.data:
            search_request = result.data[0]
            # Initialize price tracking entry
            create_price_tracking(search_request['id'])
            return search_request
        return None
    except Exception as e:
        print(f"Error creating search request: {e}")
        return None

def get_user_search_requests(user_id: str) -> List[Dict]:
    """Get all search requests for a user"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('search_requests').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting search requests: {e}")
        return []

def get_user_search_requests_with_tracking(user_id: str) -> List[Dict]:
    """
    Get all search requests for a user with price tracking and latest search results
    Optimized to reduce database queries
    
    Args:
        user_id: User ID
    
    Returns:
        List of search requests with price_tracking and latest_search_result attached
    """
    supabase = get_supabase_client()
    try:
        # Get all search requests
        requests_result = supabase.table('search_requests').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        requests = requests_result.data if requests_result.data else []
        
        if not requests:
            return []
        
        # Get all request IDs
        request_ids = [req['id'] for req in requests]
        
        # Get all price tracking entries in one query
        price_tracking_result = supabase.table('price_tracking').select('*').in_('search_request_id', request_ids).execute()
        price_tracking_map = {
            pt['search_request_id']: pt 
            for pt in (price_tracking_result.data if price_tracking_result.data else [])
        }
        
        # Get latest search results for each request
        # We'll need to do this per request since we need the most recent one
        # But we can optimize by getting all results and filtering in Python
        search_results_result = supabase.table('flight_search_results').select('*').in_('search_request_id', request_ids).order('searched_at', desc=True).execute()
        all_results = search_results_result.data if search_results_result.data else []
        
        # Create a map of latest results (first occurrence is latest due to ordering)
        latest_results_map = {}
        for result in all_results:
            req_id = result['search_request_id']
            if req_id not in latest_results_map:
                latest_results_map[req_id] = result
        
        # Attach tracking and results to requests
        for req in requests:
            req['price_tracking'] = price_tracking_map.get(req['id'])
            req['latest_search_result'] = latest_results_map.get(req['id'])
        
        return requests
    except Exception as e:
        print(f"Error getting search requests with tracking: {e}")
        return []

def get_search_request_by_id(request_id: str, user_id: str) -> Optional[Dict]:
    """Get a specific search request by ID (with user validation)"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('search_requests').select('*').eq('id', request_id).eq('user_id', user_id).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting search request: {e}")
        return None

def update_search_request(request_id: str, user_id: str, **kwargs) -> Optional[Dict]:
    """Update a search request"""
    supabase = get_supabase_client()
    try:
        # First verify ownership
        request = get_search_request_by_id(request_id, user_id)
        if not request:
            return None
        
        result = supabase.table('search_requests').update(kwargs).eq('id', request_id).execute()
        
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error updating search request: {e}")
        return None

def delete_search_request(request_id: str, user_id: str) -> bool:
    """Delete a search request (cascade will delete price_tracking)"""
    supabase = get_supabase_client()
    try:
        # First verify ownership
        request = get_search_request_by_id(request_id, user_id)
        if not request:
            return False
        
        supabase.table('search_requests').delete().eq('id', request_id).execute()
        return True
    except Exception as e:
        print(f"Error deleting search request: {e}")
        return False

def create_price_tracking(search_request_id: str) -> Optional[Dict]:
    """Create initial price tracking entry"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('price_tracking').insert({
            'search_request_id': search_request_id,
            'minimum_price': None,
            'last_checked': None,
            'last_notified_price': None
        }).execute()
        
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error creating price tracking: {e}")
        return None

def get_price_tracking(search_request_id: str) -> Optional[Dict]:
    """Get price tracking for a search request"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('price_tracking').select('*').eq('search_request_id', search_request_id).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting price tracking: {e}")
        return None

def update_price_tracking(search_request_id: str, minimum_price: Optional[float]) -> Optional[Dict]:
    """Update price tracking with new minimum price and last checked timestamp"""
    supabase = get_supabase_client()
    try:
        from datetime import datetime
        
        update_data = {
            'minimum_price': minimum_price,
            'last_checked': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('price_tracking').update(update_data).eq('search_request_id', search_request_id).execute()
        
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error updating price tracking: {e}")
        return None

def create_flight_search_result(search_request_id: str, price: Optional[float],
                                currency: str, airlines: List[str], 
                                flight_details: Dict) -> Optional[Dict]:
    """Create a new flight search result entry"""
    supabase = get_supabase_client()
    try:
        from datetime import datetime
        import json
        
        data = {
            'search_request_id': search_request_id,
            'price': price,
            'currency': currency,
            'airlines': airlines,
            'flight_details': flight_details,  # Supabase will handle JSONB
            'searched_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('flight_search_results').insert(data).execute()
        
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error creating flight search result: {e}")
        return None

def get_latest_flight_search_result(search_request_id: str) -> Optional[Dict]:
    """Get the most recent flight search result for a search request"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('flight_search_results').select('*').eq('search_request_id', search_request_id).order('searched_at', desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"Error getting flight search result: {e}")
        return None

def get_all_flight_search_results(search_request_id: str) -> List[Dict]:
    """Get all flight search results for a search request"""
    supabase = get_supabase_client()
    try:
        result = supabase.table('flight_search_results').select('*').eq('search_request_id', search_request_id).order('searched_at', desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error getting flight search results: {e}")
        return []

