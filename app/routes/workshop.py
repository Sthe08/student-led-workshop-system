from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models.user import db
from app.models.workshop import Workshop
from app.models.registration import Registration
from app.models.venue import Venue
from app.forms import WorkshopForm
from datetime import datetime, timedelta
from app.services.google_meet_service import google_meet_service
from app.services.teams_service import teams_service

workshop_bp = Blueprint('workshop', __name__)


def check_venue_availability(venue_id, date, start_time, end_time, exclude_workshop_id=None):
    """
    Check if a venue is available for a specific time slot.
    
    Args:
        venue_id: ID of the venue
        date: Date object
        start_time: datetime object for start time
        end_time: datetime object for end time
        exclude_workshop_id: ID of current workshop to exclude (when editing)
        
    Returns:
        (is_available, message)
    """
    if not venue_id:
        return True, None
    
    venue = Venue.query.get(venue_id)
    if not venue:
        return False, "Selected venue is not available."
    
    if venue.status != 'active':
        return False, f"Venue '{venue.name}' is currently under maintenance."
    
    # Fetch all scheduled workshops at this venue on the same date
    same_day_workshops = Workshop.query.filter(
        Workshop.venue_id == venue_id,
        Workshop.status == 'scheduled',
        db.func.date(Workshop.date_time) == date
    ).all()
    
    for other in same_day_workshops:
        # Skip the workshop being edited
        if exclude_workshop_id and other.id == exclude_workshop_id:
            continue
        
        # Real time-overlap check: overlap exists if start1 < end2 AND start2 < end1
        other_start = other.date_time
        other_end = other.end_time
        if start_time < other_end and other_start < end_time:
            return False, (
                f"Venue '{venue.name}' is already booked for '{other.title}' "
                f"({other_start.strftime('%H:%M')}–{other_end.strftime('%H:%M')}). "
                f"Please choose a different venue or time."
            )
    
    return True, None


def check_duplicate_registration(user_id, workshop_id):
    """
    Check if user is already registered for this workshop.
    Returns (is_duplicate, message)
    """
    existing = Registration.query.filter_by(
        user_id=user_id,
        workshop_id=workshop_id
    ).first()
    
    if existing:
        if existing.status == 'cancelled':
            return False, None
        return True, 'You are already registered for this workshop.'
    return False, None


def check_time_conflict(user_id, new_workshop):
    """
    Check if user has a time conflict with another workshop.
    Returns (has_conflict, conflicting_workshop_name)
    """
    # Get all confirmed registrations for this user
    confirmed_registrations = Registration.query.filter_by(
        user_id=user_id,
        status='confirmed'
    ).all()
    
    for registration in confirmed_registrations:
        other_workshop = registration.workshop
        
        # Skip if same workshop
        if other_workshop.id == new_workshop.id:
            continue
        
        # Check if on same date
        if other_workshop.date_time.date() != new_workshop.date_time.date():
            continue
        
        # Check time overlap
        # Time overlap exists if: start1 < end2 AND start2 < end1
        if (new_workshop.start_time < other_workshop.end_time and 
            other_workshop.start_time < new_workshop.end_time):
            return True, other_workshop.title
    
    return False, None


def check_host_conflict(host_id, date, start_time, duration_minutes, exclude_workshop_id=None):
    """
    Check if the host is already organizing another workshop at the proposed date/time.
    Returns (has_conflict, message)
    """
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    host_workshops = Workshop.query.filter(
        Workshop.host_id == host_id,
        Workshop.status == 'scheduled',
        db.func.date(Workshop.date_time) == date
    ).all()
    
    for other in host_workshops:
        if exclude_workshop_id and other.id == exclude_workshop_id:
            continue
            
        other_start = other.date_time
        other_end = other_start + timedelta(minutes=other.duration_minutes)
        
        if start_time < other_end and other_start < end_time:
            return True, f"You are already hosting '{other.title}' during this time."
            
    return False, None


def generate_google_calendar_link(workshop):
    """Generate Google Calendar deep link"""
    from urllib.parse import quote
    
    base_url = "https://calendar.google.com/render?action=TEMPLATE"
    
    # Format dates as YYYYMMDDTHHmmss
    start_date = workshop.date_time.strftime('%Y%m%dT%H%M%S')
    end_date = workshop.end_time.strftime('%Y%m%dT%H%M%S')
    
    text = quote(workshop.title)
    dates = f"{start_date}/{end_date}"
    location = quote(workshop.venue_name if workshop.venue_name else "TBA")
    details = quote(workshop.description)
    
    return f"{base_url}&text={text}&dates={dates}&location={location}&details={details}"


def generate_outlook_calendar_link(workshop):
    """Generate Outlook Web Calendar link"""
    from urllib.parse import quote
    
    base_url = "https://outlook.live.com/calendar/0/deeplink/compose"
    
    # Format dates as ISO
    start_date = workshop.date_time.isoformat()
    end_date = workshop.end_time.isoformat()
    
    subject = quote(workshop.title)
    location = quote(workshop.venue_name if workshop.venue_name else "TBA")
    
    return f"{base_url}?subject={subject}&startdt={start_date}&enddt={end_date}&location={location}"


def generate_ics_file(workshop):
    """Generate iCalendar (.ics) file content"""
    from datetime import timezone
    
    # Format dates for iCal (UTC format)
    start_date = workshop.date_time.strftime('%Y%m%dT%H%M%SZ')
    end_date = workshop.end_time.strftime('%Y%m%dT%H%M%SZ')
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    
    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Student Workshop System//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{workshop.id}@student-workshop-system
DTSTAMP:{timestamp}
DTSTART:{start_date}
DTEND:{end_date}
SUMMARY:{workshop.title}
DESCRIPTION:{workshop.description.replace(chr(10), '\\n')}
LOCATION:{workshop.venue_name if workshop.venue_name else 'TBA'}
ORGANIZER;CN=Student Workshop System:mailto:noreply@workshop.system
STATUS:CONFIRMED
SEQUENCE:0
END:VEVENT
END:VCALENDAR"""
    
    return ics_content


def generate_meeting_link(provider, date_time, duration_minutes, title='', description=''):
    """
    Generate a REAL virtual meeting link using actual API.
    Falls back to placeholder if API is not configured or fails.
    
    Args:
        provider: 'google_meet' or 'teams'
        date_time: Workshop start datetime
        duration_minutes: Duration in minutes
        title: Workshop title (for calendar event)
        description: Workshop description (for calendar event)
    
    Returns:
        (meeting_link, meeting_id, extra_data) tuple
    """
    try:
        if provider == 'google_meet':
            result = google_meet_service.create_meeting(
                title=title or 'Workshop Session',
                start_time=date_time,
                duration_minutes=duration_minutes,
                description=description or ''
            )
            
            if result.get('success'):
                return (
                    result['meet_link'],
                    result['meeting_id'],
                    {'event_id': result.get('event_id'), 'provider': 'google_meet'}
                )
            else:
                current_app.logger.warning(f'Google Meet API failed, using placeholder: {result.get("error")}')
                # Fallback to placeholder
                return generate_placeholder_link('google_meet', date_time)
                
        elif provider == 'teams':
            result = teams_service.create_meeting(
                title=title or 'Workshop Session',
                start_time=date_time,
                duration_minutes=duration_minutes,
                description=description or ''
            )
            
            if result.get('success'):
                return (
                    result['join_url'],
                    result['meeting_id'],
                    {'provider': 'teams'}
                )
            else:
                current_app.logger.warning(f'Teams API failed, using placeholder: {result.get("error")}')
                # Fallback to placeholder
                return generate_placeholder_link('teams', date_time)
        else:
            return generate_placeholder_link('generic', date_time)
            
    except Exception as e:
        current_app.logger.error(f'Meeting link generation error: {str(e)}')
        # Always fallback to placeholder on error
        return generate_placeholder_link(provider or 'generic', date_time)


def generate_placeholder_link(provider, date_time):
    """Generate placeholder link when API is not configured or fails"""
    import hashlib
    import time
    
    timestamp = str(int(time.time() * 1000))
    unique_hash = hashlib.md5(f"{timestamp}-{current_user.id}-{date_time.isoformat()}".encode()).hexdigest()[:10]
    
    if provider == 'google_meet':
        meeting_id = f"{unique_hash[:3]}-{unique_hash[3:7]}-{unique_hash[7:]}"
        return f"https://meet.google.com/{meeting_id.lower()}", meeting_id, {'placeholder': True}
    elif provider == 'teams':
        meeting_id = f"mtg_{unique_hash}"
        return f"https://teams.microsoft.com/l/meetup-join/19%3ameeting_{unique_hash}@thread.v2/0?context=%7b%22Tid%22%3a%22workshop-system%22%2c%22Oid%22%3a%22{current_user.id}%22%7d", meeting_id, {'placeholder': True}
    else:
        return f"https://meet.example.com/{unique_hash}", unique_hash, {'placeholder': True}


@workshop_bp.route('/workshops/<int:id>/download-ics')
@login_required
def download_ics(id):
    """Download workshop as .ics file"""
    from flask import make_response
    
    workshop = Workshop.query.get_or_404(id)
    
    # Check if user is registered
    registration = Registration.query.filter_by(
        user_id=current_user.id,
        workshop_id=workshop.id,
        status='confirmed'
    ).first()
    
    if not registration and current_user.id != workshop.host_id:
        flash('You must be registered for this workshop to download the calendar file.', 'warning')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Generate .ics content
    ics_content = generate_ics_file(workshop)
    
    # Create response with proper headers
    response = make_response(ics_content)
    response.headers['Content-Type'] = 'text/calendar'
    response.headers['Content-Disposition'] = f'attachment; filename="workshop_{workshop.id}.ics"'
    
    return response


@workshop_bp.route('/workshops')
def list_workshops():
    """Display all workshops with search, filtering, and pagination"""
    
    # Get filter parameters
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    date_filter = request.args.get('date', '')
    
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 6, type=int)
    
    # Base query - only show scheduled workshops
    query = Workshop.query.filter_by(status='scheduled')
    
    # Apply search filter
    if search:
        query = query.filter(
            (Workshop.title.ilike(f'%{search}%')) |
            (Workshop.description.ilike(f'%{search}%'))
        )
    
    # Apply category filter
    if category:
        query = query.filter_by(category=category)
    
    # Apply date filter (today, this_week, this_month)
    today = datetime.utcnow().date()
    if date_filter == 'today':
        query = query.filter(db.func.date(Workshop.date_time) == today)
    elif date_filter == 'this_week':
        from datetime import timedelta
        week_end = today + timedelta(days=7)
        query = query.filter(
            db.func.date(Workshop.date_time) >= today,
            db.func.date(Workshop.date_time) <= week_end
        )
    elif date_filter == 'this_month':
        from datetime import timedelta
        month_end = today + timedelta(days=30)
        query = query.filter(
            db.func.date(Workshop.date_time) >= today,
            db.func.date(Workshop.date_time) <= month_end
        )
    
    # Order by date
    query = query.order_by(Workshop.date_time.asc())
    
    # Get today's workshops separately (before pagination)
    today_workshops = Workshop.query.filter(
        Workshop.status == 'scheduled',
        db.func.date(Workshop.date_time) == today
    ).order_by(Workshop.date_time.asc()).all()
    
    # Apply pagination
    paginated_workshops = query.paginate(page=page, per_page=per_page, error_out=False)
    workshops = paginated_workshops.items
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Workshop.category).distinct().all()
    
    # Get current time for live badge
    now = datetime.utcnow()
    
    return render_template('workshops/list.html', 
                         workshops=workshops,
                         today_workshops=today_workshops,
                         categories=categories,
                         pagination=paginated_workshops,
                         search_query=search,
                         selected_category=category,
                         selected_date=date_filter,
                         current_page=page,
                         per_page=per_page,
                         now=now)


@workshop_bp.route('/workshops/<int:id>')
def view_workshop(id):
    """Display detailed information about a specific workshop"""
    
    workshop = Workshop.query.get_or_404(id)
    
    # Check if current user is registered
    is_registered = False
    if current_user.is_authenticated:
        registration = Registration.query.filter_by(
            user_id=current_user.id,
            workshop_id=workshop.id
        ).first()
        is_registered = registration is not None
    
    # Check if current user is the host
    is_host = current_user.is_authenticated and current_user.id == workshop.host_id
    
    waitlist_position = None
    if is_registered and registration.status == 'waitlisted':
        waitlist_position = Registration.query.filter_by(
            workshop_id=workshop.id,
            status='waitlisted'
        ).filter(Registration.registered_at <= registration.registered_at).count()
    
    return render_template('workshops/detail.html', 
                         workshop=workshop,
                         is_registered=is_registered,
                         is_host=is_host,
                         waitlist_position=waitlist_position,
                         generate_google_calendar_link=generate_google_calendar_link,
                         generate_outlook_calendar_link=generate_outlook_calendar_link)


@workshop_bp.route('/workshops/create', methods=['GET', 'POST'])
@login_required
def create_workshop():
    """Create a new workshop(only for approved hosts)"""
    
    # Check if user is an approved host
    if not current_user.is_host():
        flash('You must be an approved host to create a workshop.', 'warning')
        return redirect(url_for('workshop.list_workshops'))
    
    form = WorkshopForm()
    
    # Get available venues for dropdown
    available_venues = Venue.query.filter_by(status='active').order_by(Venue.name).all()
    form.venue.choices = [(v.id, f"{v.name} - {v.building} {v.room_number} (Capacity: {v.capacity})") for v in available_venues]
    
    if form.validate_on_submit():
        # Check host conflict FIRST
        has_conflict, conflict_msg = check_host_conflict(
            current_user.id,
            form.date_time.data.date(),
            form.date_time.data,
            form.duration_minutes.data
        )
        if has_conflict:
            flash(conflict_msg, 'danger')
            return redirect(url_for('workshop.create_workshop'))

        # Check workshop type
        workshop_type = form.workshop_type.data
        
        if workshop_type == 'physical':
            # Validate venue selection for physical workshops - REQUIRED
            venue_id = form.venue.data
            
            if not venue_id:
                flash('Please select a venue for your workshop.', 'danger')
                return redirect(url_for('workshop.create_workshop'))
            
            # Check venue availability
            is_available, availability_msg = check_venue_availability(
                venue_id,
                form.date_time.data.date(),
                form.date_time.data,
                form.date_time.data + timedelta(minutes=form.duration_minutes.data)
            )
            
            if not is_available:
                flash(availability_msg, 'danger')
                return redirect(url_for('workshop.create_workshop'))
            
            # Check capacity match
            venue = Venue.query.get(venue_id)
            if venue and form.capacity.data > venue.capacity:
                flash(f"Selected venue has a maximum capacity of {venue.capacity}. Please reduce workshop capacity or choose a larger venue.", 'danger')
                return redirect(url_for('workshop.create_workshop'))
            
            # Create new physical workshop
            workshop = Workshop(
                title=form.title.data,
                description=form.description.data,
                category=form.category.data,
                date_time=form.date_time.data,
                duration_minutes=form.duration_minutes.data,
                venue_id=venue_id,
                venue=None,  # Using structured venue now
                capacity=form.capacity.data,
                host_id=current_user.id,
                workshop_type='physical',
                meeting_link=None,
                meeting_id=None,
                meeting_provider=None,
                venue_status='pending'  # Require admin approval for the room booking
            )
            extra_data = None
        else:
            # Create new virtual workshop with REAL meeting link
            meeting_provider = form.meeting_provider.data
            
            # Generate meeting link with title and description for calendar integration
            meeting_link, meeting_id, extra_data = generate_meeting_link(
                provider=meeting_provider,
                date_time=form.date_time.data,
                duration_minutes=form.duration_minutes.data,
                title=form.title.data,
                description=form.description.data
            )
            
            workshop = Workshop(
                title=form.title.data,
                description=form.description.data,
                category=form.category.data,
                date_time=form.date_time.data,
                duration_minutes=form.duration_minutes.data,
                venue_id=None,
                venue=None,
                capacity=form.capacity.data,
                host_id=current_user.id,
                workshop_type='virtual',
                meeting_link=meeting_link,
                meeting_id=meeting_id,
                meeting_provider=meeting_provider
            )
        
        db.session.add(workshop)
        db.session.commit()
        
        # Check if we got a real API link or placeholder
        link_type = 'REAL' if extra_data and not extra_data.get('placeholder') else 'PLACEHOLDER'
        
        flash(f'Workshop created successfully! This is a {workshop_type} workshop. ' +
              (f'Meeting link generated ({link_type}).' if workshop_type == 'virtual' else ''), 'success')
        return redirect(url_for('workshop.view_workshop', id=workshop.id))
    
    return render_template('workshops/create.html', form=form, available_venues=available_venues)


@workshop_bp.route('/workshops/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_workshop(id):
    """Edit an existing workshop (only for host or admin)"""
    
    workshop = Workshop.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and current_user.id != workshop.host_id:
        flash('You do not have permission to edit this workshop.', 'danger')
        return redirect(url_for('workshop.view_workshop', id=workshop.id))
    
    form = WorkshopForm(obj=workshop)
    
    # Get available venues for dropdown
    available_venues = Venue.query.filter_by(status='active').order_by(Venue.name).all()
    form.venue.choices = [(v.id, f"{v.name} - {v.building} {v.room_number} (Capacity: {v.capacity})") for v in available_venues]
    
    if form.validate_on_submit():
        # Check host conflict FIRST
        has_conflict, conflict_msg = check_host_conflict(
            current_user.id,
            form.date_time.data.date(),
            form.date_time.data,
            form.duration_minutes.data,
            exclude_workshop_id=workshop.id
        )
        if has_conflict:
            flash(conflict_msg, 'danger')
            return redirect(url_for('workshop.edit_workshop', id=id))

        # Validate venue selection - REQUIRED
        venue_id = form.venue.data
        workshop_type = form.workshop_type.data
        
        if workshop_type == 'physical':
            if not venue_id:
                flash('Please select a venue for your workshop.', 'danger')
                return redirect(url_for('workshop.edit_workshop', id=id))
            
            # Check venue availability (exclude current workshop)
            is_available, availability_msg = check_venue_availability(
                venue_id,
                form.date_time.data.date(),
                form.date_time.data,
                form.date_time.data + timedelta(minutes=form.duration_minutes.data),
                exclude_workshop_id=workshop.id
            )
            
            if not is_available:
                flash(availability_msg, 'danger')
                return redirect(url_for('workshop.edit_workshop', id=id))
            
            # Check capacity match
            venue = Venue.query.get(venue_id)
            if venue and form.capacity.data > venue.capacity:
                flash(f"Selected venue has a maximum capacity of {venue.capacity}. Please reduce workshop capacity or choose a larger venue.", 'danger')
                return redirect(url_for('workshop.edit_workshop', id=id))
            
            # Update as physical workshop
            workshop.title = form.title.data
            workshop.description = form.description.data
            workshop.category = form.category.data
            workshop.date_time = form.date_time.data
            workshop.duration_minutes = form.duration_minutes.data
            
            # If venue changed, put it back to pending
            if workshop.venue_id != venue_id:
                workshop.venue_status = 'pending'
                
            workshop.venue_id = venue_id
            workshop.venue = None  # Using structured venue now
            workshop.capacity = form.capacity.data
            workshop.workshop_type = 'physical'
            # Clear virtual meeting fields
            workshop.meeting_link = None
            workshop.meeting_id = None
            workshop.meeting_provider = None
            workshop.updated_at = datetime.utcnow()
        else:
            # Update as virtual workshop
            meeting_provider = form.meeting_provider.data
            
            # Generate new meeting link if provider changed or doesn't exist
            if not workshop.meeting_link or workshop.meeting_provider != meeting_provider:
                meeting_link, meeting_id, extra_data = generate_meeting_link(
                    provider=meeting_provider,
                    date_time=form.date_time.data,
                    duration_minutes=form.duration_minutes.data,
                    title=form.title.data,
                    description=form.description.data
                )
            else:
                meeting_link = workshop.meeting_link
                meeting_id = workshop.meeting_id
            
            # Update as virtual workshop
            workshop.title = form.title.data
            workshop.description = form.description.data
            workshop.category = form.category.data
            workshop.date_time = form.date_time.data
            workshop.duration_minutes = form.duration_minutes.data
            workshop.venue_id = None
            workshop.venue = None
            workshop.capacity = form.capacity.data
            workshop.workshop_type = 'virtual'
            workshop.meeting_provider = meeting_provider
            workshop.meeting_link = meeting_link
            workshop.meeting_id = meeting_id
            workshop.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send workshop update emails and notifications to all confirmed attendees
        from app.services.email_service import send_workshop_update_email
        from app.models.notification import Notification
        
        changes_made = "The workshop details (such as date, time, or venue) were recently updated by the host."
        confirmed_registrations = Registration.query.filter_by(workshop_id=workshop.id, status='confirmed').all()
        
        for registration in confirmed_registrations:
            attendee = registration.user
            try:
                send_workshop_update_email(
                    user_email=attendee.email,
                    user_name=attendee.full_name or attendee.student_number,
                    workshop=workshop,
                    changes_made=changes_made
                )
            except Exception as e:
                current_app.logger.error(f'Failed to send update email to {attendee.email}: {e}')
                
            notification = Notification(
                user_id=attendee.id,
                notification_type='update',
                subject=f'Workshop Update: {workshop.title}',
                message=f'The workshop "{workshop.title}" has been updated. {changes_made}',
                email_sent=True
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash(f'Workshop updated successfully! Now set as {workshop_type} workshop.', 'success')
        return redirect(url_for('workshop.view_workshop', id=workshop.id))
    
    return render_template('workshops/edit.html', form=form, workshop=workshop, available_venues=available_venues)


@workshop_bp.route('/workshops/<int:id>/cancel-workshop', methods=['POST'])
@login_required
def host_cancel_workshop(id):
    """
    Allow a host or admin to permanently cancel a workshop.
    Changes status to 'cancelled' and emails all registered/waitlisted students.
    """
    workshop = Workshop.query.get_or_404(id)
    
    # Check if user is host or admin
    if not current_user.is_admin() and current_user.id != workshop.host_id:
        flash('Access denied. You can only cancel your own workshops.', 'danger')
        return redirect(url_for('workshop.view_workshop', id=workshop.id))
        
    if workshop.status != 'scheduled':
        flash('Only scheduled workshops can be cancelled.', 'warning')
        return redirect(url_for('workshop.view_workshop', id=workshop.id))
        
    workshop.status = 'cancelled'
    
    # Get all active registrations (confirmed and waitlisted)
    active_registrations = Registration.query.filter(
        Registration.workshop_id == workshop.id,
        Registration.status.in_(['confirmed', 'waitlisted'])
    ).all()
    
    from app.services.email_service import send_workshop_cancellation_email
    
    emails_sent = 0
    for reg in active_registrations:
        reg.status = 'cancelled'
        if send_workshop_cancellation_email(reg.user.email, reg.user.full_name or reg.user.username, workshop):
            emails_sent += 1
            
        # Send in-app notification
        notification = Notification(
            user_id=reg.user.id,
            notification_type='cancellation',
            subject=f'Workshop Cancelled: {workshop.title}',
            message=f'Unfortunately, the workshop "{workshop.title}" has been cancelled by the host.',
            email_sent=True
        )
        db.session.add(notification)
        
    db.session.commit()
    
    flash(f'Workshop "{workshop.title}" has been cancelled. {emails_sent} students were notified.', 'success')
    return redirect(url_for('workshop.view_workshop', id=workshop.id))


@workshop_bp.route('/workshops/<int:id>/delete', methods=['POST'])
@login_required
def delete_workshop(id):
    """Delete a workshop (only for host or admin)"""
    
    workshop = Workshop.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and current_user.id != workshop.host_id:
        flash('You do not have permission to delete this workshop.', 'danger')
        return redirect(url_for('workshop.view_workshop', id=workshop.id))
    
    db.session.delete(workshop)
    db.session.commit()
    
    flash('Workshop deleted successfully!', 'success')
    return redirect(url_for('workshop.list_workshops'))


@workshop_bp.route('/workshops/<int:id>/complete', methods=['POST'])
@login_required
def mark_complete(id):
    """Mark a workshop as completed manually by the host."""
    workshop = Workshop.query.get_or_404(id)
    
    # Check permissions
    if not current_user.is_admin() and current_user.id != workshop.host_id:
        flash('You do not have permission to update this workshop.', 'danger')
        return redirect(url_for('workshop.view_workshop', id=workshop.id))
        
    if workshop.status == 'scheduled':
        workshop.status = 'completed'
        db.session.commit()
        flash('Workshop successfully marked as completed! You can now mark attendance and request feedback.', 'success')
        
    return redirect(url_for('workshop.view_workshop', id=workshop.id))


@workshop_bp.route('/workshops/<int:id>/register', methods=['POST'])
@login_required
def register_workshop(id):
    """Register for a workshop with comprehensive conflict checking and waitlist support"""
    
    workshop = Workshop.query.get_or_404(id)
    
    # Check 2: Is user the host?
    if current_user.id == workshop.host_id:
        flash('You cannot register for your own workshop as a host.', 'warning')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Check 3: Duplicate registration (same workshop)
    is_duplicate, duplicate_msg = check_duplicate_registration(current_user.id, workshop.id)
    if is_duplicate:
        flash(duplicate_msg, 'warning')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Check 4: Time conflict with other workshops (only if getting a confirmed spot)
    has_conflict, conflicting_workshop = check_time_conflict(current_user.id, workshop)
    if has_conflict:
        flash(f'Time conflict detected! You are already registered for "{conflicting_workshop}" at the same time.', 'danger')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Check 1: Is workshop full? If yes, go to waitlist
    is_waitlisted = workshop.is_full()
    status = 'waitlisted' if is_waitlisted else 'confirmed'
    
    # Create registration
    import uuid
    registration = Registration(
        user_id=current_user.id,
        workshop_id=workshop.id,
        status=status,
        check_in_token=str(uuid.uuid4())
    )
    
    db.session.add(registration)
    if not is_waitlisted:
        workshop.registered_count += 1
    db.session.commit()
    
    # Send confirmation emails and create notification
    from app.services.email_service import send_registration_confirmation_email, send_waitlist_confirmation_email
    from app.models.notification import Notification
    
    if is_waitlisted:
        send_waitlist_confirmation_email(
            user_email=current_user.email,
            user_name=current_user.full_name or current_user.student_number,
            workshop=workshop
        )
        notification = Notification(
            user_id=current_user.id,
            notification_type='confirmation',
            subject=f'Waitlist: {workshop.title}',
            message=f'You have been added to the waitlist for {workshop.title}. We will let you know if a spot opens up.',
            email_sent=True
        )
        flash('The workshop is full. You have been added to the waitlist.', 'info')
    else:
        send_registration_confirmation_email(
            user_email=current_user.email,
            user_name=current_user.full_name or current_user.student_number,
            workshop=workshop
        )
        notification = Notification(
            user_id=current_user.id,
            notification_type='confirmation',
            subject=f'Registration Confirmed: {workshop.title}',
            message=f'You have successfully registered for {workshop.title}.',
            email_sent=True
        )
        flash('Successfully registered for the workshop! Confirmation email sent.', 'success')
        
    db.session.add(notification)
    db.session.commit()
    
    return redirect(url_for('workshop.view_workshop', id=id))


@workshop_bp.route('/workshops/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_registration(id):
    """Cancel workshop registration and handle waitlist promotion"""
    
    workshop = Workshop.query.get_or_404(id)
    
    # Find registration
    registration = Registration.query.filter_by(
        user_id=current_user.id,
        workshop_id=workshop.id
    ).first()
    
    if not registration or registration.status == 'cancelled':
        flash('You are not registered for this workshop.', 'warning')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Update registration
    was_confirmed = registration.status == 'confirmed'
    registration.status = 'cancelled'
    registration.cancelled_at = datetime.utcnow()
    
    if was_confirmed:
        workshop.registered_count -= 1
        
        # Check if anyone is on the waitlist
        first_waitlisted = Registration.query.filter_by(
            workshop_id=workshop.id,
            status='waitlisted'
        ).order_by(Registration.registered_at.asc()).first()
        
        if first_waitlisted:
            # Promote waitlisted student
            first_waitlisted.status = 'confirmed'
            workshop.registered_count += 1
            
            # Send notification
            from app.services.email_service import send_waitlist_promotion_email
            from app.models.notification import Notification
            
            promoted_user = first_waitlisted.user
            send_waitlist_promotion_email(
                user_email=promoted_user.email,
                user_name=promoted_user.full_name or promoted_user.student_number,
                workshop=workshop
            )
            
            notification = Notification(
                user_id=promoted_user.id,
                notification_type='confirmation',
                subject=f'Moved from Waitlist: {workshop.title}',
                message=f'Good news! A spot opened up for {workshop.title} and your registration is now confirmed.',
                email_sent=True
            )
            db.session.add(notification)
    
    db.session.commit()
    
    flash('Registration cancelled successfully.', 'info')
    return redirect(url_for('workshop.view_workshop', id=id))


@workshop_bp.route('/my-workshops')
@login_required
def my_workshops():
    """Display workshops organized or attended by current user with tabbed view"""
    from datetime import timedelta
    
    # Organized workshops (hosted)
    organized = Workshop.query.filter_by(host_id=current_user.id).order_by(Workshop.date_time.desc()).all()
    
    # Registered workshops with status
    registered_query = db.session.query(Registration, Workshop).join(Workshop).filter(
        Registration.user_id == current_user.id
    ).order_by(Workshop.date_time.desc())
    
    registered_with_status = []
    for reg, workshop in registered_query.all():
        registered_with_status.append({
            'id': reg.id,
            'workshop': workshop,
            'status': reg.status,
            'registered_at': reg.registered_at,
            'cancelled_at': reg.cancelled_at
        })
    
    # Categorize registered workshops
    upcoming_registered = []
    past_registered = []
    
    now = datetime.utcnow()
    
    for item in registered_with_status:
        workshop = item['workshop']
        if workshop.date_time > now:
            upcoming_registered.append(item)
        else:
            past_registered.append(item)
    
    # Categorize organized workshops
    upcoming_organized = []
    past_organized = []
    
    for workshop in organized:
        if workshop.date_time > now:
            upcoming_organized.append(workshop)
        else:
            past_organized.append(workshop)
    
    return render_template('my_workshops.html',
                         organized_workshops=organized,
                         upcoming_organized=upcoming_organized,
                         past_organized=past_organized,
                         registered_workshops=registered_with_status,
                         upcoming_registered=upcoming_registered,
                         past_registered=past_registered)
