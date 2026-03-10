from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
    
    # Timestamp when user was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Last login timestamp
    last_login = db.Column(db.DateTime)
    
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
    
    def __repr__(self):
        return f'<User {self.student_number}>'
