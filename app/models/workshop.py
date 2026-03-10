from app.models.user import db
from datetime import datetime


class Workshop(db.Model):
    """
    Workshop model for storing workshop information.
    
    This model handles the core workshop management functionality.
    """
    
    # Table name
    __tablename__ = 'workshops'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Workshop title
    title = db.Column(db.String(200), nullable=False)
    
    # Description of the workshop
    description = db.Column(db.Text, nullable=False)
    
    # Category (e.g., Programming, Design, Business, etc.)
    category = db.Column(db.String(50), nullable=False)
    
    # Date and time of the workshop
    date_time = db.Column(db.DateTime, nullable=False)
    
    # Venue/location
    venue = db.Column(db.String(200), nullable=False)
    
    # Maximum number of participants
    capacity = db.Column(db.Integer, nullable=False, default=20)
    
    # Current number of registrations
    registered_count = db.Column(db.Integer, default=0)
    
    # Workshop status: 'scheduled', 'completed', 'cancelled'
    status = db.Column(db.String(20), default='scheduled')
    
    # Host/organizer of the workshop (foreign key to users)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship to host
    host = db.relationship('User', backref=db.backref('hosted_workshops', lazy=True))
    
    # Timestamp when workshop was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamp when workshop was last updated
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to registrations
    registrations = db.relationship('Registration', backref='workshop', lazy=True, cascade='all, delete-orphan')
    
    def is_full(self):
        """Check if workshop has reached capacity"""
        return self.registered_count >= self.capacity
    
    def available_spots(self):
        """Return number of available spots"""
        return self.capacity - self.registered_count
    
    def __repr__(self):
        return f'<Workshop {self.title}>'
