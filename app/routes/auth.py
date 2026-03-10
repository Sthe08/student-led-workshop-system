from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app.models.user import db
from app.forms import RegistrationForm, LoginForm, ProfileForm
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route.
    
    Allows new users to create an account with student number, email, and password.
    Users can choose their role: student or host (requires admin approval).
    """
    # If user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Create new user
        user = User(
            student_number=form.student_number.data,
            email=form.email.data,
            full_name=form.full_name.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        # If user selected host role, they need admin approval
        if form.role.data == 'host':
            user.approved_host = False
            flash('Your host request will be reviewed by an administrator.', 'info')
        else:
            user.approved_host = True  # Students are automatically approved
        
        # Save to database
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route.
    
    Authenticates users with their student number/email and password.
    """
    # If user is already logged in, redirect to home page
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Find user by student number or email
        user = User.query.filter(
            (User.student_number == form.student_number.data) | 
            (User.email == form.student_number.data)
        ).first()
        
        # Check if user exists and password is correct
        if user and user.check_password(form.password.data):
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log in the user
            login_user(user, remember=form.remember_me.data)
            
            # Flash success message
            flash(f'Welcome back, {user.full_name or user.student_number}!', 'success')
            
            # Redirect to next page or home page
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid student number/email or password.', 'danger')
    
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout route.
    
    Logs out the current user and redirects to home page.
    """
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    User profile page.
    
    Allows users to view and edit their profile information.
    """
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Update user profile
        current_user.full_name = form.full_name.data
        current_user.bio = form.bio.data
        
        # Save changes
        db.session.commit()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('profile.html', form=form)


@auth_bp.route('/admin/approve-hosts', methods=['GET', 'POST'])
@login_required
def approve_hosts():
    """
    Admin page to approve host requests.
    
    Only accessible by admin users.
    """
    # Check if user is admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all pending host requests
    pending_hosts = User.query.filter_by(role='host', approved_host=False).all()
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')  # 'approve' or 'reject'
        
        user = User.query.get(user_id)
        if user:
            if action == 'approve':
                user.approved_host = True
                flash(f'Host request for {user.full_name} has been approved.', 'success')
            elif action == 'reject':
                # Optionally delete the user or just keep them as unapproved
                flash(f'Host request for {user.full_name} has been rejected.', 'info')
            
            db.session.commit()
        
        return redirect(url_for('auth.approve_hosts'))
    
    return render_template('admin/approve_hosts.html', pending_hosts=pending_hosts)


@auth_bp.route('/admin/users')
@login_required
def manage_users():
    """
   Admin page to view all users(read-only).
    
    Only accessible by admin users.
    """
    # Check if user is admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all users ordered by registration date
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Calculate statistics
    total_users = len(users)
    students_count = User.query.filter_by(role='student').count()
    hosts_count = User.query.filter_by(role='host').count()
    admins_count = User.query.filter_by(role='admin').count()
    
    return render_template('admin/user_management.html', 
                         users=users,
                         total_users=total_users,
                         students_count=students_count,
                         hosts_count=hosts_count,
                         admins_count=admins_count)
