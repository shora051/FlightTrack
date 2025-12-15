from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import SignupForm, LoginForm
from app.database import create_user, get_user_by_email
from app.mail import send_mailgun_email

auth_bp = Blueprint('auth', __name__)

def _get_serializer() -> URLSafeTimedSerializer:
    """Create a URLSafeTimedSerializer for verification tokens."""
    secret_key = current_app.config['SECRET_KEY']
    return URLSafeTimedSerializer(secret_key)


def _generate_verification_token(user: dict) -> str:
    """Generate a signed token containing pending user data for email verification."""
    serializer = _get_serializer()
    return serializer.dumps(user, salt='email-verify')


def _send_verification_email(user: dict) -> bool:
    """Send verification email to user via Mailgun."""
    token = _generate_verification_token(user)
    verify_url = url_for('auth.verify', token=token, _external=True)
    subject = "Verify your FlightTrack email"
    text = (
        "Welcome to FlightTrack!\n\n"
        f"Please verify your email by clicking the link below:\n{verify_url}\n\n"
        "This link will expire in 24 hours."
    )
    html = (
        f"<p>Welcome to FlightTrack!</p>"
        f"<p>Please verify your email by clicking the link below:</p>"
        f"<p><a href=\"{verify_url}\">{verify_url}</a></p>"
        f"<p>This link will expire in 24 hours.</p>"
    )
    sent_ok = send_mailgun_email(user['email'], subject, text, html)
    return sent_ok


def _load_token(token: str, max_age_seconds: int = 86400):
    """Validate a token and return payload or None on error."""
    serializer = _get_serializer()
    try:
        return serializer.loads(token, max_age=max_age_seconds, salt='email-verify')
    except SignatureExpired:
        flash('Verification link has expired. Please request a new one.', 'warning')
    except BadSignature:
        flash('Invalid verification link.', 'danger')
    return None


def login_required(f):
    """Decorator to require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            flash('An account with this email already exists. Please log in.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Hash password and send verification email with pending payload
        password_hash = generate_password_hash(password)
        pending_user = {'email': email, 'password_hash': password_hash}
        sent = _send_verification_email(pending_user)
        if sent:
            flash('Please check your email to verify your account.', 'success')
        else:
            flash('We could not send a verification email. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
    
    return render_template('signup.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if already logged in
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        
        # Get user from database
        user = get_user_by_email(email)
        
        if user and check_password_hash(user['password_hash'], password):
            # Log user in
            session['user_id'] = user['id']
            session['email'] = user['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@auth_bp.route('/verify')
def verify():
    token = request.args.get('token')
    if not token:
        flash('Missing verification token.', 'danger')
        return redirect(url_for('auth.login'))
    
    payload = _load_token(token)
    if not payload:
        return redirect(url_for('auth.login'))

    # If already verified, just log in
    existing = get_user_by_email(payload.get('email'))
    if existing:
        session['user_id'] = existing['id']
        session['email'] = existing['email']
        flash('Email already verified. You are now logged in.', 'info')
        return redirect(url_for('dashboard.index'))

    # Create verified user now
    created = create_user(payload.get('email'), payload.get('password_hash'))
    if created:
        session['user_id'] = created['id']
        session['email'] = created['email']
        flash('Email verified! You are now logged in.', 'success')
        return redirect(url_for('dashboard.index'))

    flash('Could not verify account. Please try again.', 'danger')
    return redirect(url_for('auth.login'))



