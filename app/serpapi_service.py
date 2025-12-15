"""
SerpAPI service for searching flights using Google Flights API
"""
import re
import requests
from flask import current_app
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from app.constants import (
    SERPAPI_TRIP_TYPE_ROUND_TRIP,
    SERPAPI_TRIP_TYPE_ONE_WAY,
    DEFAULT_CURRENCY,
    API_TIMEOUT,
)

# Mapping of airline names to IATA codes for SerpAPI
AIRLINE_NAME_TO_IATA = {
    'Delta': 'DL',
    'United': 'UA',
    'American': 'AA',
    'Southwest': 'WN',
    'JetBlue': 'B6',
    'Alaska': 'AS',
    'Hawaiian': 'HA',
    'Frontier': 'F9',
    'Spirit': 'NK',
    'Allegiant': 'G4',
    'Lufthansa': 'LH',
    'British Airways': 'BA',
    'Air France': 'AF',
    'KLM': 'KL',
    'Emirates': 'EK',
    'Qatar Airways': 'QR',
    'Etihad': 'EY',
    'Turkish Airlines': 'TK',
    'Singapore Airlines': 'SQ',
    'Cathay Pacific': 'CX',
    'Japan Airlines': 'JL',
    'ANA': 'NH',
    'Korean Air': 'KE',
    'Qantas': 'QF',
    'Air Canada': 'AC',
    'Aeromexico': 'AM',
    'LATAM': 'LA',
    'Virgin Atlantic': 'VS',
    'Iberia': 'IB',
    'Swiss': 'LX',
    'Austrian': 'OS',
    'Scandinavian': 'SK'
}

# Alliance keywords supported by SerpApi include_airlines
ALLIANCE_CODES = {'STAR_ALLIANCE', 'SKYTEAM', 'ONEWORLD'}

# IATA code: two uppercase letters or one uppercase letter + one digit
VALID_AIRLINE_CODE_PATTERN = re.compile(r'^[A-Z]{2}$|^[A-Z][0-9]$')

def convert_airline_names_to_codes(airline_names: List[str]) -> Tuple[List[str], List[str]]:
    """
    Convert airline names to valid SerpApi include_airlines codes.

    Returns:
        (valid_codes, invalid_values)
    """
    codes: List[str] = []
    invalid: List[str] = []

    for name in airline_names:
        raw = AIRLINE_NAME_TO_IATA.get(name, name)
        code = raw.strip().upper() if isinstance(raw, str) else ''
        if not code:
            continue

        if code in ALLIANCE_CODES or VALID_AIRLINE_CODE_PATTERN.match(code):
            codes.append(code)
        else:
            # Keep track of values we intentionally skip to avoid sending bad params
            invalid.append(code)

    # Deduplicate while preserving order to avoid bloating the query string
    seen = set()
    unique_codes = []
    for code in codes:
        if code not in seen:
            seen.add(code)
            unique_codes.append(code)

    return unique_codes, invalid

def search_flights(depart_from: str, arrive_at: str, departure_date: str,
                   return_date: Optional[str] = None, passengers: int = 1,
                   preferred_airlines: Optional[List[str]] = None) -> Optional[Dict]:
    """
    Search for flights using SerpAPI Google Flights API
    
    Args:
        depart_from: Origin airport code (e.g., 'JFK')
        arrive_at: Destination airport code (e.g., 'LAX')
        departure_date: Departure date in YYYY-MM-DD format
        return_date: Return date in YYYY-MM-DD format (optional)
        passengers: Number of passengers (default: 1)
        preferred_airlines: List of preferred airline names (optional)
    
    Returns:
        Dictionary containing flight search results, or None if error
    """
    api_key = current_app.config.get('SERPAPI_KEY')
    
    if not api_key:
        print("SERPAPI_KEY not configured")
        return None
    
    # Build API request parameters
    # Using minimal required parameters to avoid 400 errors
    params = {
        'engine': 'google_flights',
        'api_key': api_key,
        'departure_id': depart_from,
        'arrival_id': arrive_at,
        'outbound_date': departure_date,
        'adults': passengers
    }
    
    # Set trip type: 1 = Round trip, 2 = One way
    # According to SerpAPI docs, type defaults to 1 (Round trip), but return_date is required for round trips
    if return_date:
        params['type'] = SERPAPI_TRIP_TYPE_ROUND_TRIP
        params['return_date'] = return_date
    else:
        params['type'] = SERPAPI_TRIP_TYPE_ONE_WAY
    
    # Add preferred airlines if provided
    # SerpAPI uses 'include_airlines' parameter with IATA codes (e.g., "DL" for Delta)
    if preferred_airlines and len(preferred_airlines) > 0:
        airline_codes, invalid_airlines = convert_airline_names_to_codes(preferred_airlines)
        if airline_codes:
            params['include_airlines'] = ','.join(airline_codes)
        if invalid_airlines:
            # Log invalid entries for debugging; do not send them to SerpApi
            print(f"Skipped invalid airline entries for SerpApi include_airlines: {invalid_airlines}")
    
    try:
        # Make API request
        response = requests.get('https://serpapi.com/search', params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Extract cheapest flight from results
        cheapest_flight = extract_cheapest_flight(data)

        # Attach a shareable search URL if SerpApi provides one
        search_url = None
        meta = data.get('search_metadata', {}) if isinstance(data, dict) else {}
        if isinstance(meta, dict):
            search_url = meta.get('google_flights_url') or meta.get('serpapi_url')
        if cheapest_flight is not None and search_url and not cheapest_flight.get('link'):
            cheapest_flight['link'] = search_url
        
        return {
            'success': True,
            'cheapest_flight': cheapest_flight,
            'raw_data': data,
            'searched_at': datetime.utcnow().isoformat()
        }
    
    except requests.exceptions.HTTPError as e:
        error_msg = str(e)
        # Try to get more details from the response
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"SerpAPI error details: {error_detail}")
                # Extract error message if available
                if isinstance(error_detail, dict):
                    if 'error' in error_detail:
                        error_msg = error_detail['error']
                    elif 'message' in error_detail:
                        error_msg = error_detail['message']
            except:
                error_text = e.response.text
                print(f"SerpAPI error response: {error_text}")
                if error_text:
                    error_msg = error_text[:200]  # Limit error message length
        return {
            'success': False,
            'error': error_msg,
            'searched_at': datetime.utcnow().isoformat()
        }
    except requests.exceptions.RequestException as e:
        print(f"Error calling SerpAPI: {e}")
        return {
            'success': False,
            'error': str(e),
            'searched_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"Unexpected error in flight search: {e}")
        return {
            'success': False,
            'error': str(e),
            'searched_at': datetime.utcnow().isoformat()
        }

def extract_cheapest_flight(data: Dict) -> Optional[Dict]:
    """
    Extract the cheapest flight from SerpAPI response
    
    Args:
        data: Raw response from SerpAPI
    
    Returns:
        Dictionary with cheapest flight details, or None if no flights found
    """
    try:
        # SerpAPI Google Flights response structure
        # The response may have different structures, so we'll handle multiple cases
        
        # Check for best_flights (common structure)
        if 'best_flights' in data and len(data['best_flights']) > 0:
            best_flight = data['best_flights'][0]
            return parse_flight_data(best_flight)
        
        # Check for other_flights
        if 'other_flights' in data and len(data['other_flights']) > 0:
            # Sort by price and get cheapest
            flights = data['other_flights']
            cheapest = min(flights, key=lambda x: float(x.get('price', {}).get('total', float('inf'))))
            return parse_flight_data(cheapest)
        
        # Check for flights array
        if 'flights' in data and len(data['flights']) > 0:
            flights = data['flights']
            cheapest = min(flights, key=lambda x: float(x.get('price', {}).get('total', float('inf'))))
            return parse_flight_data(cheapest)
        
        # If no flights found in expected structure, return None
        print("No flights found in SerpAPI response")
        return None
    
    except Exception as e:
        print(f"Error extracting cheapest flight: {e}")
        return None

def parse_flight_data(flight_data: Dict) -> Dict:
    """
    Parse flight data from SerpAPI response into a standardized format
    
    Args:
        flight_data: Flight data from SerpAPI response
    
    Returns:
        Dictionary with standardized flight information
    """
    try:
        # Extract price
        price_info = flight_data.get('price', {})
        price = None
        currency = DEFAULT_CURRENCY
        
        if isinstance(price_info, dict):
            price = float(price_info.get('total', 0)) if price_info.get('total') else None
            currency = price_info.get('currency', DEFAULT_CURRENCY)
        elif isinstance(price_info, (int, float)):
            price = float(price_info)
        
        # Extract flight segments
        outbound_segments = []
        return_segments = []
        
        # Handle outbound flights
        if 'flights' in flight_data:
            outbound_segments = parse_segments(flight_data['flights'])
        
        # Handle return flights (if round trip)
        if 'return_flights' in flight_data:
            return_segments = parse_segments(flight_data['return_flights'])
        
        # Extract airline information
        airlines = []
        if outbound_segments:
            for segment in outbound_segments:
                if segment.get('airline') and segment['airline'] not in airlines:
                    airlines.append(segment['airline'])
        
        # Extract duration
        duration = flight_data.get('duration', {})
        total_duration = None
        if isinstance(duration, dict):
            total_duration = duration.get('total', None)
        elif isinstance(duration, (int, float)):
            total_duration = duration
        
        # Extract stops information
        stops = flight_data.get('stops', 0)
        
        return {
            'price': price,
            'currency': currency,
            'airlines': airlines,
            'outbound_segments': outbound_segments,
            'return_segments': return_segments,
            'duration': total_duration,
            'stops': stops,
            'link': flight_data.get('link', ''),
            'raw_data': flight_data
        }
    
    except Exception as e:
        print(f"Error parsing flight data: {e}")
        return {
            'price': None,
            'currency': DEFAULT_CURRENCY,
            'airlines': [],
            'outbound_segments': [],
            'return_segments': [],
            'duration': None,
            'stops': 0,
            'link': '',
            'raw_data': flight_data,
            'error': str(e)
        }

def parse_segments(segments: List[Dict]) -> List[Dict]:
    """
    Parse flight segments from SerpAPI response
    
    Args:
        segments: List of flight segments
    
    Returns:
        List of parsed segment dictionaries
    """
    parsed_segments = []
    
    for segment in segments:
        try:
            parsed_segment = {
                'departure_airport': segment.get('departure_airport', {}).get('id', ''),
                'departure_time': segment.get('departure_airport', {}).get('time', ''),
                'arrival_airport': segment.get('arrival_airport', {}).get('id', ''),
                'arrival_time': segment.get('arrival_airport', {}).get('time', ''),
                'airline': segment.get('airline', ''),
                'flight_number': segment.get('flight_number', ''),
                'duration': segment.get('duration', None)
            }
            parsed_segments.append(parsed_segment)
        except Exception as e:
            print(f"Error parsing segment: {e}")
            continue
    
    return parsed_segments
