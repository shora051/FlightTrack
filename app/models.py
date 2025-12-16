"""
Data models and helper functions for database entities
"""

from typing import Optional, Dict, List
from datetime import datetime

class User:
    """User model"""
    def __init__(self, id: str, email: str, password_hash: str, created_at: Optional[str] = None):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create User from dictionary"""
        return cls(
            id=data['id'],
            email=data['email'],
            password_hash=data['password_hash'],
            created_at=data.get('created_at')
        )

class SearchRequest:
    """Search request model"""
    def __init__(self, id: str, user_id: str, depart_from: str, arrive_at: str,
                 departure_date: str, return_date: Optional[str],
                 trip_type: str, preferred_airlines: Optional[List[str]],
                 stops: int = 0, created_at: Optional[str] = None):
        self.id = id
        self.user_id = user_id
        self.depart_from = depart_from
        self.arrive_at = arrive_at
        self.departure_date = departure_date
        self.return_date = return_date
        self.trip_type = trip_type
        self.preferred_airlines = preferred_airlines or []
        self.stops = stops
        self.created_at = created_at
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create SearchRequest from dictionary"""
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            depart_from=data['depart_from'],
            arrive_at=data['arrive_at'],
            departure_date=data['departure_date'],
            return_date=data.get('return_date'),
            trip_type=data['trip_type'],
            preferred_airlines=data.get('preferred_airlines'),
            stops=data.get('stops', 0),
            created_at=data.get('created_at')
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'depart_from': self.depart_from,
            'arrive_at': self.arrive_at,
            'departure_date': self.departure_date,
            'return_date': self.return_date,
            'trip_type': self.trip_type,
            'preferred_airlines': self.preferred_airlines,
            'stops': self.stops,
            'created_at': self.created_at
        }

class PriceTracking:
    """Price tracking model - now includes latest search result data"""
    def __init__(self, id: str, search_request_id: str, minimum_price: Optional[float],
                 last_checked: Optional[str], last_notified_price: Optional[float],
                 latest_price: Optional[float] = None, currency: str = 'USD',
                 airlines: Optional[List[str]] = None, flight_details: Optional[Dict] = None):
        self.id = id
        self.search_request_id = search_request_id
        self.minimum_price = minimum_price
        self.last_checked = last_checked
        self.last_notified_price = last_notified_price
        self.latest_price = latest_price
        self.currency = currency
        self.airlines = airlines or []
        self.flight_details = flight_details or {}
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create PriceTracking from dictionary"""
        return cls(
            id=data['id'],
            search_request_id=data['search_request_id'],
            minimum_price=float(data['minimum_price']) if data.get('minimum_price') else None,
            last_checked=data.get('last_checked'),
            last_notified_price=float(data['last_notified_price']) if data.get('last_notified_price') else None,
            latest_price=float(data['latest_price']) if data.get('latest_price') else None,
            currency=data.get('currency', 'USD'),
            airlines=data.get('airlines', []),
            flight_details=data.get('flight_details', {})
        )

