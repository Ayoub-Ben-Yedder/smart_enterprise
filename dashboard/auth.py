import hashlib
import logging
from functools import wraps
from flask import session, request, jsonify, redirect, url_for
from database import DatabaseManager

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password, password_hash):
        """Verify password against hash."""
        return self._hash_password(password) == password_hash
    
    def login_required(self, f):
        """Decorator to require login for routes."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def authenticate_user(self, username, password):
        """Authenticate user with username and password."""
        if not username or not password:
            return False, "Username and password are required"
        
        user = self.db_manager.get_user_by_username(username)
        
        if user and self._verify_password(password, user[2]):
            session['user_id'] = user[0]
            session['username'] = user[1]
            logger.info(f"User {username} logged in successfully")
            return True, "Login successful"
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return False, "Invalid username or password"
    
    def logout_user(self):
        """Logout current user."""
        session.clear()
        return True, "Logout successful"
