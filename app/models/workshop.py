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
    
    # Duration in minutes (default 60 minutes)
    duration_minutes = db.Column(db.Integer, default=60, nullable=False)
    
    # Venue/location (text field for backward compatibility)
    venue = db.Column(db.String(200), nullable=True)
    
    # Venue foreign key (for structured venue management)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=True)
    
    # Maximum number of participants
    capacity = db.Column(db.Integer, nullable=False, default=20)
    
    # Current number of registrations
    registered_count = db.Column(db.Integer, default=0)
    
    # Workshop status: 'scheduled', 'completed', 'cancelled'
    status = db.Column(db.String(20), default='scheduled')
    
    # Venue booking status: 'pending', 'approved', 'rejected'
    venue_status = db.Column(db.String(20), default='approved')
    
    # Workshop type: 'physical', 'virtual'
    workshop_type = db.Column(db.String(20), default='physical')
    
    # Virtual meeting link (for virtual workshops)
    meeting_link = db.Column(db.String(500), nullable=True)
    
    # Meeting ID from provider (Google Meet/Teams)
    meeting_id = db.Column(db.String(100), nullable=True)
    
    # Meeting provider: 'google_meet', 'teams'
    meeting_provider = db.Column(db.String(20), nullable=True)
    
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
    
    @property
    def start_time(self):
        """Get workshop start time"""
        return self.date_time
    
    @property
    def end_time(self):
        """Calculate workshop end time based on duration"""
        from datetime import timedelta
        return self.date_time + timedelta(minutes=self.duration_minutes)
    
    @property
    def venue_name(self):
        """Get venue name from venue_details or fallback to text venue field"""
        if self.venue_details:
            return f"{self.venue_details.name} ({self.venue_details.building} {self.venue_details.room_number})"
        return self.venue if self.venue else "TBA"
    
    def is_full(self):
        """Check if workshop has reached capacity"""
        return self.registered_count >= self.capacity
    
    def available_spots(self):
        """Return number of available spots"""
        return self.capacity - self.registered_count
    
    def is_virtual(self):
        """Check if workshop is virtual"""
        return self.workshop_type == 'virtual'
    
    def get_meeting_link(self):
        """Get meeting link for virtual workshops"""
        if self.is_virtual() and self.meeting_link:
            return self.meeting_link
        return None
    
    def get_meeting_provider_icon(self):
        """Get FontAwesome icon for meeting provider"""
        if self.meeting_provider == 'google_meet':
            return 'fab fa-google'
        elif self.meeting_provider == 'teams':
            return 'fas fa-video'
        return 'fas fa-video'
    
    def __repr__(self):
        return f'<Workshop {self.title}>'
