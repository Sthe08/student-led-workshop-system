from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.user import db
from app.models.workshop import Workshop
from app.models.registration import Registration
from app.forms import WorkshopForm
from datetime import datetime

workshop_bp = Blueprint('workshop', __name__)


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
    
    # Apply pagination
    paginated_workshops = query.paginate(page=page, per_page=per_page, error_out=False)
    workshops = paginated_workshops.items
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Workshop.category).distinct().all()
    
    return render_template('workshops/list.html', 
                         workshops=workshops,
                         categories=categories,
                         pagination=paginated_workshops,
                         search_query=search,
                         selected_category=category,
                         selected_date=date_filter,
                         current_page=page,
                         per_page=per_page)


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
    
    return render_template('workshops/detail.html', 
                         workshop=workshop,
                         is_registered=is_registered,
                         is_host=is_host)


@workshop_bp.route('/workshops/create', methods=['GET', 'POST'])
@login_required
def create_workshop():
    """Create a new workshop(only for approved hosts)"""
    
    # Check if user is an approved host
    if not current_user.is_host():
        flash('You must be an approved host to create a workshop.', 'warning')
        return redirect(url_for('workshop.list_workshops'))
    
    form = WorkshopForm()
    
    if form.validate_on_submit():
        # Create new workshop
        workshop = Workshop(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            date_time=form.date_time.data,
            venue=form.venue.data,
            capacity=form.capacity.data,
            host_id=current_user.id
        )
        
        db.session.add(workshop)
        db.session.commit()
        
        flash('Workshop created successfully!', 'success')
        return redirect(url_for('workshop.view_workshop', id=workshop.id))
    
    return render_template('workshops/create.html', form=form)


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
    
    if form.validate_on_submit():
        # Update workshop
        workshop.title = form.title.data
        workshop.description = form.description.data
        workshop.category = form.category.data
        workshop.date_time = form.date_time.data
        workshop.venue = form.venue.data
        workshop.capacity = form.capacity.data
        workshop.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Workshop updated successfully!', 'success')
        return redirect(url_for('workshop.view_workshop', id=workshop.id))
    
    return render_template('workshops/edit.html', form=form, workshop=workshop)


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


@workshop_bp.route('/workshops/<int:id>/register', methods=['POST'])
@login_required
def register_workshop(id):
    """Register for a workshop"""
    
    workshop = Workshop.query.get_or_404(id)
    
    # Check if workshop is full
    if workshop.is_full():
        flash('Sorry, this workshop is full.', 'warning')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Check if already registered
    existing_registration = Registration.query.filter_by(
        user_id=current_user.id,
        workshop_id=workshop.id
    ).first()
    
    if existing_registration:
        flash('You are already registered for this workshop.', 'info')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Check if user is the host
    if current_user.id == workshop.host_id:
        flash('You cannot register for your own workshop as a host.', 'warning')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Create registration
    registration = Registration(
        user_id=current_user.id,
        workshop_id=workshop.id,
        status='confirmed'
    )
    
    db.session.add(registration)
    workshop.registered_count += 1
    db.session.commit()
    
    flash('Successfully registered for the workshop!', 'success')
    return redirect(url_for('workshop.view_workshop', id=id))


@workshop_bp.route('/workshops/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_registration(id):
    """Cancel workshop registration"""
    
    workshop = Workshop.query.get_or_404(id)
    
    # Find registration
    registration = Registration.query.filter_by(
        user_id=current_user.id,
        workshop_id=workshop.id
    ).first()
    
    if not registration:
        flash('You are not registered for this workshop.', 'warning')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Update registration
    registration.status = 'cancelled'
    registration.cancelled_at = datetime.utcnow()
    workshop.registered_count -= 1
    
    db.session.commit()
    
    flash('Registration cancelled successfully.', 'info')
    return redirect(url_for('workshop.view_workshop', id=id))


@workshop_bp.route('/my-workshops')
@login_required
def my_workshops():
    """Display workshops organized or attended by current user"""
    
    # Organized workshops
    organized = Workshop.query.filter_by(host_id=current_user.id).order_by(Workshop.date_time.desc()).all()
    
    # Registered workshops
    registered_workshops = []
    registrations = Registration.query.filter_by(user_id=current_user.id).all()
    for reg in registrations:
        registered_workshops.append(reg.workshop)
    
    return render_template('my_workshops.html',
                         organized_workshops=organized,
                         registered_workshops=registered_workshops)
