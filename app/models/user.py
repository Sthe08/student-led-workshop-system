from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    User model for the Student-Led Workshop System.
    
    This model stores user information and handles authentication.
    Roles: 'student', 'host', 'admin'
    """
    
    # Table name
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Student number (unique identifier for students)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    
    # Email address
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # Hashed password
    password_hash = db.Column(db.String(255), nullable=False)
    
    # User role: 'student', 'host', or 'admin'
    role = db.Column(db.String(20), nullable=False, default='student')
    
    # Host approval status (only relevant if role is 'host')
    approved_host = db.Column(db.Boolean, default=False)
    
    # Profile information
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    
    # POPIA Compliance Fields
    # Consent tracking
    consent_notifications = db.Column(db.Boolean, default=False)  # Opt-in for notifications
    consent_data_processing = db.Column(db.Boolean, default=False)  # Required for service
    consent_cookie_policy = db.Column(db.Boolean, default=False)  # Cookie acceptance
    privacy_policy_accepted = db.Column(db.Boolean, default=False)  # Privacy policy acceptance
    
    # Data rights tracking
    account_active = db.Column(db.Boolean, default=True)  # Soft delete support
    last_data_access = db.Column(db.DateTime)  # Last time user accessed their data
    data_export_requested = db.Column(db.Boolean, default=False)  # Data portability request
    deletion_requested = db.Column(db.Boolean, default=False)  # Right to be forgotten
    deletion_scheduled_date = db.Column(db.DateTime)  # When account will be deleted
    
    # Timestamp when user was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Last login timestamp
    last_login = db.Column(db.DateTime)
    
    # Account updated timestamp
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Data retention: mark for auto-deletion after X years of inactivity
    inactive_since = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_host(self):
        """Check if user is a host"""
        return self.role == 'host' and self.approved_host
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin'
    
    def mark_inactive(self):
        """Mark user as inactive (soft delete)"""
        self.account_active = False
        self.inactive_since = datetime.utcnow()
    
    def request_data_deletion(self, days_until_deletion=30):
        """Schedule account for deletion (right to be forgotten)"""
        self.deletion_requested = True
        self.deletion_scheduled_date = datetime.utcnow() + timedelta(days=days_until_deletion)
    
    def cancel_deletion_request(self):
        """Cancel deletion request"""
        self.deletion_requested = False
        self.deletion_scheduled_date = None
    
    def update_last_data_access(self):
        """Track when user last accessed their data"""
        self.last_data_access = datetime.utcnow()
    
    def __repr__(self):
        return f'<User {self.student_number}>'
