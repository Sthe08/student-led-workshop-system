from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.user import db
from app.models.venue import Venue
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/venue-bookings')
@login_required
def manage_venue_bookings():
    """Admin dashboard to approve or reject pending venue bookings."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
        
    from app.models.workshop import Workshop
    pending_workshops = Workshop.query.filter_by(workshop_type='physical', venue_status='pending').order_by(Workshop.date_time.asc()).all()
    
    return render_template('admin/venue_bookings.html', pending_workshops=pending_workshops)


@admin_bp.route('/admin/venue-bookings/<int:id>/approve', methods=['POST'])
@login_required
def approve_venue_booking(id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
        
    from app.models.workshop import Workshop
    workshop = Workshop.query.get_or_404(id)
    
    workshop.venue_status = 'approved'
    db.session.commit()
    
    from app.services.email_service import send_venue_approval_email
    send_venue_approval_email(workshop, approved=True)
    
    flash(f'Workshop "{workshop.title}" venue booking approved.', 'success')
    return redirect(url_for('admin.manage_venue_bookings'))


@admin_bp.route('/admin/venue-bookings/<int:id>/reject', methods=['POST'])
@login_required
def reject_venue_booking(id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
        
    from app.models.workshop import Workshop
    workshop = Workshop.query.get_or_404(id)
    
    workshop.venue_status = 'rejected'
    db.session.commit()
    
    from app.services.email_service import send_venue_approval_email
    send_venue_approval_email(workshop, approved=False)
    
    flash(f'Workshop "{workshop.title}" venue booking rejected.', 'warning')
    return redirect(url_for('admin.manage_venue_bookings'))



@admin_bp.route('/admin/venues')
@login_required
def manage_venues():
    """
    Admin page to view all venues.
    
    Only accessible by admin users.
    """
    # Check if user is admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all venues ordered by name
    venues = Venue.query.order_by(Venue.name.asc()).all()
    
    return render_template('admin/venue_management.html', venues=venues)


@admin_bp.route('/admin/venues/create', methods=['GET', 'POST'])
@login_required
def create_venue():
    """
    Admin page to create a new venue.
    
    Only accessible by admin users.
    """
    # Check if user is admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        building = request.form.get('building')
        room_number = request.form.get('room_number')
        capacity = request.form.get('capacity', type=int)
        facilities = request.form.get('facilities')
        description = request.form.get('description')
        status = request.form.get('status', 'active')
        
        # Validate required fields
        if not all([name, building, room_number, capacity]):
            flash('Name, Building, Room Number, and Capacity are required.', 'danger')
            return redirect(url_for('admin.create_venue'))
        
        # Create new venue
        venue = Venue(
            name=name,
            building=building,
            room_number=room_number,
            capacity=capacity,
            facilities=facilities,
            description=description,
            status=status
        )
        
        db.session.add(venue)
        db.session.commit()
        
        flash(f'Venue "{name}" created successfully!', 'success')
        return redirect(url_for('admin.manage_venues'))
    
    return render_template('admin/venue_form.html', venue=None, action='create')


@admin_bp.route('/admin/venues/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_venue(id):
    """
    Admin page to edit an existing venue.
    
    Only accessible by admin users.
    """
    # Check if user is admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    venue = Venue.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update venue data
        venue.name = request.form.get('name')
        venue.building = request.form.get('building')
        venue.room_number = request.form.get('room_number')
        venue.capacity = request.form.get('capacity', type=int)
        venue.facilities = request.form.get('facilities')
        venue.description = request.form.get('description')
        venue.status = request.form.get('status', 'active')
        venue.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Venue "{venue.name}" updated successfully!', 'success')
        return redirect(url_for('admin.manage_venues'))
    
    return render_template('admin/venue_form.html', venue=venue, action='edit')


@admin_bp.route('/admin/venues/<int:id>/delete', methods=['POST'])
@login_required
def delete_venue(id):
    """
    Admin route to delete a venue.
    
    Only accessible by admin users.
    """
    # Check if user is admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    venue = Venue.query.get_or_404(id)
    
    # Check if venue is being used by any workshops
    if venue.workshops:
        flash(f'Cannot delete venue "{venue.name}" because it is assigned to {len(venue.workshops)} workshop(s).', 'danger')
        return redirect(url_for('admin.manage_venues'))
    
    db.session.delete(venue)
    db.session.commit()
    
    flash(f'Venue "{venue.name}" deleted successfully!', 'success')
    return redirect(url_for('admin.manage_venues'))


@admin_bp.route('/admin/venues/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_venue_status(id):
    """
    Admin route to toggle venue status (active/maintenance).
    
    Only accessible by admin users.
    """
    # Check if user is admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    venue = Venue.query.get_or_404(id)
    
    # Toggle status
    if venue.status == 'active':
        venue.status = 'maintenance'
        flash(f'Venue "{venue.name}" marked as under maintenance.', 'warning')
    else:
        venue.status = 'active'
        flash(f'Venue "{venue.name}" is now active.', 'success')
    
    db.session.commit()
    return redirect(url_for('admin.manage_venues'))
