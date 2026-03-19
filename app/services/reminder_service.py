from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.models.user import db
from app.models.workshop import Workshop
from app.models.registration import Registration
from app.models.notification import Notification
from app.services.email_service import send_workshop_reminder_email
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def send_reminders():
    """Send 24-hour and 1-hour reminders for upcoming workshops"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        now = datetime.utcnow()
        
        # Workshops starting in 24 hours
        workshops_24h = Workshop.query.filter(
            Workshop.status == 'scheduled',
            Workshop.date_time >= now + timedelta(hours=23),
            Workshop.date_time <= now + timedelta(hours=25)
        ).all()
    
        # Workshops starting in 1 hour
        workshops_1h = Workshop.query.filter(
            Workshop.status == 'scheduled',
            Workshop.date_time >= now + timedelta(minutes=59),
            Workshop.date_time <= now + timedelta(minutes=61)
        ).all()
        
        emails_sent = 0
        
        # Send 24-hour reminders
        for workshop in workshops_24h:
            confirmed_registrations = Registration.query.filter_by(
                workshop_id=workshop.id,
                status='confirmed'
            ).all()
        
            for registration in confirmed_registrations:
                user = registration.user
                
                # Send email
                if send_workshop_reminder_email(
                    user_email=user.email,
                    user_name=user.full_name or user.student_number,
                    workshop=workshop,
                    hours_before=24
                ):
                    emails_sent += 1
            
                # Create notification
                notification = Notification(
                    user_id=user.id,
                    notification_type='reminder',
                    subject=f'{workshop.title} starts in 24 hours',
                    message=f'Reminder: Your workshop "{workshop.title}" starts tomorrow at {workshop.date_time.strftime("%I:%M %p")}.',
                    email_sent=True
                )
                db.session.add(notification)
        
        # Send 1-hour reminders
        for workshop in workshops_1h:
            confirmed_registrations = Registration.query.filter_by(
                workshop_id=workshop.id,
                status='confirmed'
            ).all()
            
            for registration in confirmed_registrations:
                user = registration.user
                
                # Send email
                if send_workshop_reminder_email(
                    user_email=user.email,
                    user_name=user.full_name or user.student_number,
                    workshop=workshop,
                    hours_before=1
                ):
                    emails_sent += 1
            
                # Create notification
                notification = Notification(
                    user_id=user.id,
                    notification_type='reminder',
                    subject=f'{workshop.title} starts in 1 hour',
                    message=f'Reminder: Your workshop "{workshop.title}" starts in 1 hour at {workshop.date_time.strftime("%I:%M %p")}.',
                    email_sent=True
                )
                db.session.add(notification)
        
        db.session.commit()
        logger.info(f'Sent {emails_sent} reminder emails')
        
        # Complete past workshops
        past_workshops = Workshop.query.filter(
            Workshop.status == 'scheduled',
            Workshop.date_time <= now - timedelta(hours=4)
        ).all()
    
        completed_count = 0
        for w in past_workshops:
            w.status = 'completed'
            completed_count += 1
        
        
        if completed_count > 0:
            db.session.commit()
            logger.info(f'Marked {completed_count} past workshops as completed')


def init_scheduler(app):
    """Initialize the scheduler"""
    with app.app_context():
        # Run every hour
        scheduler.add_job(
            send_reminders,
            trigger=CronTrigger(minute=0),
            id='workshop_reminders',
            replace_existing=True
        )
        scheduler.start()
        logger.info('Reminder scheduler started')
