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
    
    # Unique constraint to prevent duplicate registrations
    __table_args__ = (db.UniqueConstraint('user_id', 'workshop_id', name='unique_user_workshop'),)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('registrations', lazy=True))
    
    def __repr__(self):
        return f'<Registration User:{self.user_id} Workshop:{self.workshop_id}>'
