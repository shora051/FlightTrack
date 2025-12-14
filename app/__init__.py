from flask import Flask
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
    app.config['SUPABASE_KEY'] = os.getenv('SUPABASE_KEY')
    app.config['SERPAPI_KEY'] = os.getenv('SERPAPI_KEY')
    
    # Register blueprints
    from app.auth import auth_bp
    from app.dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    
    # Home route
    @app.route('/')
    def index():
        from flask import render_template, session
        return render_template('index.html', logged_in='user_id' in session)
    
    return app

