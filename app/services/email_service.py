from flask_mail import Message
from flask import render_template, current_app
from threading import Thread
import logging

logger = logging.getLogger(__name__)


def send_async_email(app, msg):
    """Send email asynchronously in a background thread"""
    with app.app_context():
        try:
            from app import mail
            mail.send(msg)
            logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")


def send_email(to, subject, template=None, html_body=None, text_body=None, **kwargs):
    """
    Send an email.
    
    Args:
        to: Recipient email address
        subject: Email subject
        template: Email template name (optional, if html_body/text_body are not provided)
        html_body: Pre-rendered HTML body (optional)
        text_body: Pre-rendered plain text body (optional)
        kwargs: Template variables (if template is used)
    """
    try:
        # Create message
        msg = Message(subject, recipients=[to])
        
        if html_body and text_body:
            msg.html = html_body
            msg.body = text_body
        elif template:
            # Render HTML body
            msg.html = render_template(f'email/{template}.html', **kwargs)
            
            # Render text body
            msg.body = render_template(f'email/{template}.txt', **kwargs)
        else:
            logger.error(f"Error sending email to {to}: No template or pre-rendered bodies provided.")
            return False
        
        # Send in background thread using current_app
        app = current_app._get_current_object()
        thread = Thread(target=send_async_email, args=(app, msg))
        thread.start()
        
        return True
    except Exception as e:
        logger.error(f"Error sending email to {to}: {str(e)}")
        return False


def send_registration_confirmation_email(user_email, user_name, workshop):
    """Send registration confirmation email"""
    from app.services.email_service import generate_google_calendar_link, generate_outlook_calendar_link
    
    subject = f'Workshop Registration Confirmation - {workshop.title}'
    
    # Generate calendar links
    google_calendar_url = generate_google_calendar_link(workshop)
    outlook_calendar_url = generate_outlook_calendar_link(workshop)
    
    return send_email(
        to=user_email,
        subject=subject,
        template='registration_confirmation',
        user_name=user_name,
        workshop=workshop,
        google_calendar_url=google_calendar_url,
        outlook_calendar_url=outlook_calendar_url
    )


def send_workshop_reminder_email(user_email, user_name, workshop, hours_before=24):
    """Send workshop reminder email"""
    subject = f'Reminder: {workshop.title} starts in {hours_before} hours'
    
    return send_email(
        to=user_email,
        subject=subject,
        template='workshop_reminder',
        user_name=user_name,
        workshop=workshop,
        hours_before=hours_before
    )


def send_broadcast_message_email(user_email, user_name, workshop, message, host_name):
    """Send broadcast message from host to attendee"""
    subject = f'Announcement from {workshop.title} Host'
    
    return send_email(
        to=user_email,
        subject=subject,
        template='broadcast_message',
        user_name=user_name,
        workshop=workshop,
        message=message,
        host_name=host_name
    )


def send_workshop_update_email(user_email, user_name, workshop, changes_made):
    """Send workshop update notification email"""
    subject = f'Workshop Update: {workshop.title}'
    
    return send_email(
        to=user_email,
        subject=subject,
        template='workshop_update',
        user_name=user_name,
        workshop=workshop,
        changes_made=changes_made
    )


def send_workshop_cancellation_email(user_email, user_name, workshop):
    """Send workshop cancellation notification email"""
    subject = f'Workshop Cancelled: {workshop.title}'
    
    return send_email(
        to=user_email,
        subject=subject,
        template='workshop_cancelled',
        user_name=user_name,
        workshop=workshop
    )


def send_venue_approval_email(workshop, approved=True, reason=None):
    """Send notification to workshop host about venue approval/rejection"""
    host = workshop.host
    status_text = "Approved" if approved else "Rejected"
    subject = f"Venue Booking {status_text}: {workshop.title}"
    
    return send_email(
        to=host.email,
        subject=subject,
        template='venue_approval',
        host_name=host.full_name or host.username,
        workshop=workshop,
        approved=approved,
        reason=reason
    )


def generate_google_calendar_link(workshop):
    """Generate Google Calendar deep link"""
    from urllib.parse import quote
    
    base_url = "https://calendar.google.com/render?action=TEMPLATE"
    start_date = workshop.date_time.strftime('%Y%m%dT%H%M%S')
    end_date = workshop.end_time.strftime('%Y%m%dT%H%M%S')
    
    text = quote(workshop.title)
    dates = f"{start_date}/{end_date}"
    location = quote(workshop.venue_name if workshop.venue_name else "TBA")
    details = quote(workshop.description)
    
    return f"{base_url}&text={text}&dates={dates}&location={location}&details={details}"


def send_waitlist_confirmation_email(user_email, user_name, workshop):
    """Send confirmation that user is on the waitlist"""
    subject = f'Waitlist Confirmation - {workshop.title}'
    
    return send_email(
        to=user_email,
        subject=subject,
        template='waitlist_confirmation',
        user_name=user_name,
        workshop=workshop
    )


def send_waitlist_promotion_email(user_email, user_name, workshop):
    """Send notification that user was promoted from waitlist to confirmed"""
    from app.services.email_service import generate_google_calendar_link, generate_outlook_calendar_link
    
    subject = f'You are IN! Workshop Registration Confirmed - {workshop.title}'
    
    # Generate calendar links
    google_calendar_url = generate_google_calendar_link(workshop)
    outlook_calendar_url = generate_outlook_calendar_link(workshop)
    
    return send_email(
        to=user_email,
        subject=subject,
        template='waitlist_promotion',
        user_name=user_name,
        workshop=workshop,
        google_calendar_url=google_calendar_url,
        outlook_calendar_url=outlook_calendar_url
    )


def generate_outlook_calendar_link(workshop):
    """Generate Outlook Web Calendar link"""
    from urllib.parse import quote
    
    base_url = "https://outlook.live.com/calendar/0/deeplink/compose"
    start_date = workshop.date_time.isoformat()
    end_date = workshop.end_time.isoformat()
    
    subject = quote(workshop.title)
    location = quote(workshop.venue_name if workshop.venue_name else "TBA")
    
    return f"{base_url}?subject={subject}&startdt={start_date}&enddt={end_date}&location={location}"
