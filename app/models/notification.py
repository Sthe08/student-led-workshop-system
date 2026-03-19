from app.models.user import db
from datetime import datetime


class Notification(db.Model):
    """
    Notification model for in-app notifications.
    
    Stores all notifications sent to users with delivery status.
    """
    
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # 'broadcast', 'reminder', 'confirmation', 'update', 'cancellation'
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    email_sent = db.Column(db.Boolean, default=False)
    email_delivered = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'


class BroadcastMessage(db.Model):
    """
    Broadcast message model for host announcements.
    
    Stores messages sent by hosts to workshop attendees.
    """
    
    __tablename__ = 'broadcast_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    workshop_id = db.Column(db.Integer, db.ForeignKey('workshops.id'), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    recipient_count = db.Column(db.Integer, default=0)
    
    # Relationships
    workshop = db.relationship('Workshop', backref=db.backref('broadcast_messages', lazy=True))
    host = db.relationship('User', backref=db.backref('broadcast_messages', lazy=True))
    
    def __repr__(self):
        return f'<BroadcastMessage {self.id} for Workshop {self.workshop_id}>'
