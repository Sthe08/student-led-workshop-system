from app.models.user import db
from datetime import datetime


class AuditLog(db.Model):
    """
    Audit Log model for POPIA compliance.
    
    Tracks all data access and modifications for accountability.
    Required by POPIA Section 19 - Security of Personal Information.
    """
    
    # Table name
    __tablename__ = 'audit_logs'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Timestamp of the action
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # User who performed the action (if authenticated)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationship to user
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))
    
    # Action type: CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, etc.
    action_type = db.Column(db.String(50), nullable=False)
    
    # Entity affected (e.g., 'user', 'workshop', 'registration')
    entity_type = db.Column(db.String(50))
    
    # ID of the affected entity
    entity_id = db.Column(db.Integer)
    
    # Description of what happened
    description = db.Column(db.Text)
    
    # IP address where action originated
    ip_address = db.Column(db.String(45))
    
    # User agent (browser/device info)
    user_agent = db.Column(db.String(500))
    
    # Additional details (JSON format)
    additional_info = db.Column(db.Text)
    
    # Success status
    success = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<AuditLog {self.id} - {self.action_type} at {self.timestamp}>'
    
    @staticmethod
    def log_action(user_id=None, action_type='UNKNOWN', entity_type=None, 
                   entity_id=None, description='', ip_address=None, 
                   user_agent=None, additional_info=None, success=True):
        """
        Static method to create and save an audit log entry.
        
        Usage:
            AuditLog.log_action(
                user_id=current_user.id,
                action_type='VIEW_PROFILE',
                entity_type='user',
                entity_id=current_user.id,
                description=f'User {current_user.student_number} viewed their profile',
                ip_address=request.remote_addr,
                success=True
            )
        """
        log = AuditLog(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_info=additional_info,
            success=success
        )
        db.session.add(log)
        db.session.commit()
