from app.models.user import db
from datetime import datetime


class Attendance(db.Model):
    """
    Attendance model for tracking student attendance at workshops.
    
    This model manages attendance records and links to feedback.
    """
    
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'), nullable=False)
    status = db.Column(db.String(20), default='absent')  # 'present', 'absent', 'late'
    checked_in_at = db.Column(db.DateTime)
    marked_by_host_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('attendance_records', lazy=True))
    workshop = db.relationship('Workshop', backref=db.backref('attendance_records', lazy=True))
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'workshop_id', name='unique_user_workshop_attendance'),)
    
    def mark_present(self):
        """Mark attendee as present"""
        self.status = 'present'
        self.checked_in_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Attendance User:{self.user_id} Workshop:{self.workshop_id} Status:{self.status}>'


class Feedback(db.Model):
    """
    Feedback model for storing student ratings and comments.
    
    Only attendees marked as 'present' can submit feedback.
    """
    
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    comment = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('feedback_submissions', lazy=True))
    workshop = db.relationship('Workshop', backref=db.backref('feedback_entries', lazy=True))
    
    # Unique constraint - one feedback per user per workshop
    __table_args__ = (db.UniqueConstraint('user_id', 'workshop_id', name='unique_user_workshop_feedback'),)
    
    def __repr__(self):
        return f'<Feedback {self.rating} stars for Workshop {self.workshop_id} from User {self.user_id}>'
