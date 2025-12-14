from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, RadioField, SelectMultipleField, DateField, PasswordField
from wtforms.validators import DataRequired, Email, NumberRange, ValidationError, Optional
from datetime import date

# Common airlines list for the dropdown
AIRLINES = [
    ('Delta', 'Delta'),
    ('United', 'United'),
    ('American', 'American Airlines'),
    ('Southwest', 'Southwest'),
    ('JetBlue', 'JetBlue'),
    ('Alaska', 'Alaska Airlines'),
    ('Hawaiian', 'Hawaiian Airlines'),
    ('Frontier', 'Frontier'),
    ('Spirit', 'Spirit Airlines'),
    ('Allegiant', 'Allegiant Air')
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
    depart_from = StringField('Depart From', validators=[DataRequired()],
                             render_kw={'placeholder': 'Airport code (e.g., JFK) or city name (e.g., New York)'})
    arrive_at = StringField('Arrive At', validators=[DataRequired()],
                           render_kw={'placeholder': 'Airport code (e.g., LAX) or city name (e.g., Los Angeles)'})
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

