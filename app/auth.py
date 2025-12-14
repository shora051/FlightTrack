from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app.forms import SignupForm, LoginForm
from app.database import create_user, get_user_by_email

auth_bp = Blueprint('auth', __name__)

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
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Create user
        user = create_user(email, password_hash)
        
        if user:
            # Log user in
            session['user_id'] = user['id']
            session['email'] = user['email']
            flash('Account created successfully!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('An error occurred. Please try again.', 'danger')
    
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

