from app.models.user import db
from datetime import datetime


class Venue(db.Model):
    """
    Venue model for managing physical locations and rooms.
    
    This model handles venue booking and availability checking.
    """
    
    # Table name
    __tablename__ = 'venues'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Venue name (e.g., "Computer Lab 1", "Conference Room A")
    name = db.Column(db.String(100), nullable=False)
    
    # Building name (e.g., "Engineering Building", "Library")
    building = db.Column(db.String(100), nullable=False)
    
    # Room number or identifier
    room_number = db.Column(db.String(20), nullable=False)
    
    # Maximum capacity of the venue
    capacity = db.Column(db.Integer, nullable=False)
    
    # Available facilities (comma-separated or JSON)
    facilities = db.Column(db.Text)
    
    # Venue status: 'active', 'inactive', 'maintenance'
    status = db.Column(db.String(20), default='active')
    
    # Description of the venue
    description = db.Column(db.Text)
    
    # Relationship to workshops
    workshops = db.relationship('Workshop', backref='venue_details', lazy=True)
    
    # Timestamp when venue was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamp when venue was last updated
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Venue {self.name} ({self.building} {self.room_number})>'
    
    def is_available(self, date, start_time, end_time):
        """
        Check if venue is available for a specific time slot.
        
        Args:
            date: Date object
            start_time: datetime object for start time
            end_time: datetime object for end time
            
        Returns:
            Boolean indicating availability
        """
        from app.models.workshop import Workshop
        
        # Check for conflicting workshops
        conflict = Workshop.query.filter(
            Workshop.venue_id == self.id,
            Workshop.status == 'scheduled',
            db.func.date(Workshop.date_time) == date,
            Workshop.start_time < end_time,
            Workshop.end_time > start_time
        ).first()
        
        return conflict is None
    
    def get_facilities_list(self):
        """Return facilities as a list"""
        if self.facilities:
            return [f.strip() for f in self.facilities.split(',')]
        return []
