from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.user import db
from app.models.workshop import Workshop
from app.models.registration import Registration
from app.models.notification import Notification, BroadcastMessage
from app.services.email_service import send_broadcast_message_email
from datetime import datetime

notification_bp = Blueprint('notification', __name__)


@notification_bp.route('/workshops/<int:id>/broadcast', methods=['GET', 'POST'])
@login_required
def send_broadcast(id):
    """Host sends broadcast message to all confirmed attendees"""
    workshop = Workshop.query.get_or_404(id)
    
    # Check if user is the host or admin
    if not current_user.is_admin() and current_user.id != workshop.host_id:
        flash('You do not have permission to send broadcasts for this workshop.', 'danger')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    if request.method == 'POST':
        message_text = request.form.get('message')
        
        if not message_text or len(message_text.strip()) == 0:
            flash('Message cannot be empty.', 'warning')
            return redirect(url_for('workshop.view_workshop', id=id))
        
        if len(message_text) > 500:
            flash('Message must be 500 characters or less.', 'warning')
            return redirect(url_for('workshop.view_workshop', id=id))
        
        # Get all confirmed attendees
        confirmed_registrations = Registration.query.filter_by(
            workshop_id=workshop.id,
            status='confirmed'
        ).all()
        
        if not confirmed_registrations:
            flash('No confirmed attendees to send the message to.', 'info')
            return redirect(url_for('workshop.view_workshop', id=id))
        
        # Create broadcast message record
        broadcast = BroadcastMessage(
            workshop_id=workshop.id,
            host_id=current_user.id,
            message=message_text,
            recipient_count=len(confirmed_registrations)
        )
        db.session.add(broadcast)
        
        # Send emails and create notifications for each attendee
        emails_sent = 0
        notifications_created = 0
        
        for registration in confirmed_registrations:
            attendee = registration.user
            
            # Send email
            if send_broadcast_message_email(
                user_email=attendee.email,
                user_name=attendee.full_name or attendee.student_number,
                workshop=workshop,
                message=message_text,
                host_name=current_user.full_name or current_user.student_number
            ):
                emails_sent += 1
            
            # Create in-app notification
            notification = Notification(
                user_id=attendee.id,
                notification_type='broadcast',
                subject=f'Announcement from {workshop.title}',
                message=message_text,
                email_sent=True
            )
            db.session.add(notification)
            notifications_created += 1
        
        db.session.commit()
        
        flash(f'Broadcast sent! {emails_sent} emails delivered, {notifications_created} notifications created.', 'success')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # GET request - show broadcast form
    attendee_count = Registration.query.filter_by(
        workshop_id=workshop.id,
        status='confirmed'
    ).count()
    
    return render_template('workshops/broadcast_form.html', 
                         workshop=workshop, 
                         attendee_count=attendee_count)


@notification_bp.route('/notifications')
@login_required
def view_notifications():
    """View current user's notifications"""
    # Get all notifications for current user
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(50).all()
    
    # Mark all as read
    unread_count = 0
    for notification in notifications:
        if not notification.is_read:
            notification.mark_as_read()
            unread_count += 1
    
    if unread_count > 0:
        db.session.commit()
    
    return render_template('notifications/list.html', notifications=notifications)


@notification_bp.route('/notifications/<int:id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(id):
    """Mark a specific notification as read"""
    notification = Notification.query.get_or_404(id)
    
    # Only allow user to mark their own notifications
    if notification.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.mark_as_read()
    db.session.commit()
    
    return jsonify({'success': True})


@notification_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in notifications:
        notification.mark_as_read()
    
    db.session.commit()
    
    return jsonify({'success': True, 'marked_count': len(notifications)})


@notification_bp.route('/notifications/unread-count')
@login_required
def get_unread_count():
    """Get count of unread notifications (for badge display)"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'unread_count': count})
