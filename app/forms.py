from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, RadioField, SelectMultipleField, SelectField, DateField, PasswordField
from wtforms.validators import DataRequired, Email, NumberRange, ValidationError, Optional
from datetime import date

# Hardcoded airports list for dropdowns
AIRPORTS = [
    # Major US Airports
    ('ATL', 'ATL - Hartsfield-Jackson Atlanta International Airport'),
    ('LAX', 'LAX - Los Angeles International Airport'),
    ('ORD', 'ORD - Chicago O\'Hare International Airport'),
    ('DFW', 'DFW - Dallas/Fort Worth International Airport'),
    ('DEN', 'DEN - Denver International Airport'),
    ('JFK', 'JFK - John F. Kennedy International Airport'),
    ('SFO', 'SFO - San Francisco International Airport'),
    ('SEA', 'SEA - Seattle-Tacoma International Airport'),
    ('LAS', 'LAS - McCarran International Airport'),
    ('MIA', 'MIA - Miami International Airport'),
    ('CLT', 'CLT - Charlotte Douglas International Airport'),
    ('PHX', 'PHX - Phoenix Sky Harbor International Airport'),
    ('IAH', 'IAH - George Bush Intercontinental Airport'),
    ('MCO', 'MCO - Orlando International Airport'),
    ('EWR', 'EWR - Newark Liberty International Airport'),
    ('MSP', 'MSP - Minneapolis-Saint Paul International Airport'),
    ('DTW', 'DTW - Detroit Metropolitan Airport'),
    ('PHL', 'PHL - Philadelphia International Airport'),
    ('LGA', 'LGA - LaGuardia Airport'),
    ('BWI', 'BWI - Baltimore/Washington International Airport'),
    ('SLC', 'SLC - Salt Lake City International Airport'),
    ('DCA', 'DCA - Ronald Reagan Washington National Airport'),
    ('MDW', 'MDW - Chicago Midway International Airport'),
    ('HNL', 'HNL - Daniel K. Inouye International Airport'),
    ('BOS', 'BOS - Logan International Airport'),
    ('IAD', 'IAD - Washington Dulles International Airport'),
    ('FLL', 'FLL - Fort Lauderdale-Hollywood International Airport'),
    ('SAN', 'SAN - San Diego International Airport'),
    ('TPA', 'TPA - Tampa International Airport'),
    ('PDX', 'PDX - Portland International Airport'),
    # Major International Airports
    ('LHR', 'LHR - London Heathrow Airport'),
    ('CDG', 'CDG - Paris Charles de Gaulle Airport'),
    ('FRA', 'FRA - Frankfurt Airport'),
    ('AMS', 'AMS - Amsterdam Airport Schiphol'),
    ('DXB', 'DXB - Dubai International Airport'),
    ('NRT', 'NRT - Narita International Airport'),
    ('HND', 'HND - Tokyo Haneda Airport'),
    ('ICN', 'ICN - Incheon International Airport'),
    ('SIN', 'SIN - Singapore Changi Airport'),
    ('HKG', 'HKG - Hong Kong International Airport'),
    ('SYD', 'SYD - Sydney Kingsford Smith Airport'),
    ('MEL', 'MEL - Melbourne Airport'),
    ('YYZ', 'YYZ - Toronto Pearson International Airport'),
    ('YVR', 'YVR - Vancouver International Airport'),
    ('MEX', 'MEX - Mexico City International Airport'),
    ('GRU', 'GRU - São Paulo/Guarulhos International Airport'),
    ('EZE', 'EZE - Buenos Aires Ministro Pistarini International Airport'),
    ('LGW', 'LGW - London Gatwick Airport'),
    ('MAD', 'MAD - Madrid-Barajas Airport'),
    ('FCO', 'FCO - Rome Fiumicino Airport'),
    ('BCN', 'BCN - Barcelona-El Prat Airport'),
    ('ZUR', 'ZUR - Zurich Airport'),
    ('VIE', 'VIE - Vienna International Airport'),
    ('DOH', 'DOH - Hamad International Airport'),
    ('AUH', 'AUH - Abu Dhabi International Airport'),
    ('IST', 'IST - Istanbul Airport'),
    ('DME', 'DME - Moscow Domodedovo Airport'),
    ('PEK', 'PEK - Beijing Capital International Airport'),
    ('PVG', 'PVG - Shanghai Pudong International Airport'),
]

# Expanded airlines list for the dropdown
AIRLINES = [
    # US Airlines
    ('Delta', 'Delta Air Lines'),
    ('United', 'United Airlines'),
    ('American', 'American Airlines'),
    ('Southwest', 'Southwest Airlines'),
    ('JetBlue', 'JetBlue Airways'),
    ('Alaska', 'Alaska Airlines'),
    ('Hawaiian', 'Hawaiian Airlines'),
    ('Frontier', 'Frontier Airlines'),
    ('Spirit', 'Spirit Airlines'),
    ('Allegiant', 'Allegiant Air'),
    # International Airlines
    ('Lufthansa', 'Lufthansa'),
    ('British Airways', 'British Airways'),
    ('Air France', 'Air France'),
    ('KLM', 'KLM Royal Dutch Airlines'),
    ('Emirates', 'Emirates'),
    ('Qatar Airways', 'Qatar Airways'),
    ('Etihad', 'Etihad Airways'),
    ('Turkish Airlines', 'Turkish Airlines'),
    ('Singapore Airlines', 'Singapore Airlines'),
    ('Cathay Pacific', 'Cathay Pacific'),
    ('Japan Airlines', 'Japan Airlines'),
    ('ANA', 'All Nippon Airways'),
    ('Korean Air', 'Korean Air'),
    ('Qantas', 'Qantas'),
    ('Air Canada', 'Air Canada'),
    ('Aeromexico', 'Aeroméxico'),
    ('LATAM', 'LATAM Airlines'),
    ('Virgin Atlantic', 'Virgin Atlantic'),
    ('Iberia', 'Iberia'),
    ('Swiss', 'Swiss International Air Lines'),
    ('Austrian', 'Austrian Airlines'),
    ('Scandinavian', 'Scandinavian Airlines'),
]

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    
    def validate_confirm_password(self, field):
        if self.password.data != field.data:
            raise ValidationError('Passwords must match.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class SearchRequestForm(FlaskForm):
    depart_from = SelectField('Depart From', choices=AIRPORTS, validators=[DataRequired()])
    arrive_at = SelectField('Arrive At', choices=AIRPORTS, validators=[DataRequired()])
    departure_date = DateField('Departure Date', validators=[DataRequired()],
                               format='%Y-%m-%d')
    return_date = DateField('Return Date', validators=[Optional()],
                           format='%Y-%m-%d')
    passengers = IntegerField('Passengers', validators=[DataRequired(), NumberRange(min=1, max=9)])
    trip_type = RadioField('Trip Type', choices=[('one_way', 'One Way'), ('round_trip', 'Round Trip')],
                          validators=[DataRequired()], default='round_trip')
    preferred_airlines = SelectMultipleField('Preferred Airlines', choices=AIRLINES,
                                            validators=[Optional()])
    
    def validate_return_date(self, field):
        if self.trip_type.data == 'round_trip':
            if not field.data:
                raise ValidationError('Return date is required for round trip.')
            if self.departure_date.data and field.data and field.data < self.departure_date.data:
                raise ValidationError('Return date must be on or after departure date.')
    
    def validate_departure_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError('Departure date cannot be in the past.')

