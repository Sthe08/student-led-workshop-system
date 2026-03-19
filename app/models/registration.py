from app.models.user import db
from datetime import datetime


class Registration(db.Model):
    """
    Registration model for tracking student registrations to workshops.
    
    This model manages the relationship between users and workshops.
    """
    
    # Table name
    __tablename__ = 'registrations'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Foreign key to workshop
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'), nullable=False)
    
    # Registration status: 'confirmed', 'cancelled', 'waitlisted'
    status = db.Column(db.String(20), default='confirmed')
    
    # Registration timestamp
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Cancellation timestamp (if applicable)
    cancelled_at = db.Column(db.DateTime)
    
    # Check-in token (unique UUID for QR code)
    check_in_token = db.Column(db.String(36), unique=True, nullable=True)
    
    # Attendance status
    checked_in = db.Column(db.Boolean, default=False)
    
    # Check-in timestamp
    check_in_time = db.Column(db.DateTime)
    
    # Unique constraint to prevent duplicate registrations
    __table_args__ = (db.UniqueConstraint('user_id', 'workshop_id', name='unique_user_workshop'),)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('registrations', lazy=True))
    
    def __repr__(self):
        return f'<Registration User:{self.user_id} Workshop:{self.workshop_id}>'
    
    def generate_token(self):
        """Generate a new unique check-in token if one doesn't exist"""
        import uuid
        if not self.check_in_token:
            self.check_in_token = str(uuid.uuid4())
            return True
        return False
