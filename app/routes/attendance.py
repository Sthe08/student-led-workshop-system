from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app.models.user import db, User
from app.models.workshop import Workshop
from app.models.registration import Registration
from app.models.attendance import Attendance, Feedback
from app.forms import FeedbackForm
from datetime import datetime, timedelta
import csv
import io
from sqlalchemy import func, extract

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/workshops/<int:id>/qr/<int:registration_id>')
@login_required
def serve_qr_code(id, registration_id):
    """Serve a QR code image for a given registration"""
    import qrcode
    from io import BytesIO
    from flask import send_file, request

    workshop = Workshop.query.get_or_404(id)
    registration = Registration.query.get_or_404(registration_id)
    
    # Security check: User can only see their own QR code, or host/admin can see any
    if not current_user.is_admin() and current_user.id != workshop.host_id and current_user.id != registration.user_id:
        flash("You do not have permission to view this QR code.", "danger")
        return redirect(url_for('workshop.view_workshop', id=id))

    # Ensure token exists
    if not registration.check_in_token:
        # Fallback just in case
        registration.generate_token()
        db.session.commit()

    # Generate the check-in URL for the host to scan
    # It must be absolute URL so phone scanner goes to the right place
    checkin_url = url_for('attendance.qr_checkin', id=id, token=registration.check_in_token, _external=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(checkin_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')


@attendance_bp.route('/workshops/<int:id>/checkin/<token>')
@login_required
def qr_checkin(id, token):
    """Student check-in via QR scan (usually scanned by host or student's own phone)"""
    workshop = Workshop.query.get_or_404(id)
    
    # Optionally, restrict scanner to be the Host or Admin if you want only hosts to scan
    # But usually, if it's "self check-in", the student scans a printed QR code. 
    # Currently the model is "Host scans student's QR code on their phone" based on earlier requirement ("host manually ticks names -> QR code on students phones")
    # Actually, allow anyone logged in to process the check-in if they hold the token.
    
    registration = Registration.query.filter_by(check_in_token=token, workshop_id=id).first()
    
    if not registration:
        flash("Invalid check-in QR code.", "danger")
        return redirect(url_for('workshop.view_workshop', id=id))
        
    if registration.status != 'confirmed':
        flash("Registration is not confirmed.", "warning")
        return redirect(url_for('workshop.view_workshop', id=id))
        
    if registration.checked_in:
        flash(f"{registration.user.full_name or registration.user.student_number} is already checked in.", "info")
        return render_template('attendance/checkin_success.html', workshop=workshop, registration=registration, already_checked_in=True)

    # Mark check-in
    registration.checked_in = True
    registration.check_in_time = datetime.utcnow()
    
    # Also create an Attendance record for consistency with existing system
    attendance = Attendance.query.filter_by(user_id=registration.user_id, workshop_id=id).first()
    if not attendance:
        attendance = Attendance(user_id=registration.user_id, workshop_id=id)
        db.session.add(attendance)
    
    attendance.status = 'present'
    attendance.marked_by_student_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f"Check-in successful for {registration.user.full_name or registration.user.student_number}!", "success")
    return render_template('attendance/checkin_success.html', workshop=workshop, registration=registration, already_checked_in=False)


@attendance_bp.route('/workshops/<int:id>/checkin-dashboard')
@login_required
def checkin_dashboard(id):
    """Live dashboard for host to see check-ins"""
    workshop = Workshop.query.get_or_404(id)
    
    if not current_user.is_admin() and current_user.id != workshop.host_id:
        flash("Only the host can view the check-in dashboard.", "danger")
        return redirect(url_for('workshop.view_workshop', id=id))
        
    registrations = Registration.query.filter_by(workshop_id=id, status='confirmed').all()
    
    return render_template('attendance/checkin_dashboard.html', workshop=workshop, registrations=registrations)



@attendance_bp.route('/workshops/<int:id>/attendance', methods=['GET', 'POST'])
@login_required
def manage_attendance(id):
    """Host manages attendance for their workshop"""
    workshop = Workshop.query.get_or_404(id)
    
    # Check if user is the host or admin
    if not current_user.is_admin() and current_user.id != workshop.host_id:
        flash('You do not have permission to manage attendance for this workshop.', 'danger')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Get all registered students
    registrations = Registration.query.filter_by(
        workshop_id=workshop.id,
        status='confirmed'
    ).all()
    
    if request.method == 'POST':
        # Mark attendance for selected students
        marked_count = 0
        for registration in registrations:
            attendance_status = request.form.get(f'attendance_{registration.user_id}')
            
            # Get or create attendance record
            attendance = Attendance.query.filter_by(
                user_id=registration.user_id,
                workshop_id=workshop.id
            ).first()
            
            if not attendance:
                attendance = Attendance(
                    user_id=registration.user_id,
                    workshop_id=workshop.id
                )
                db.session.add(attendance)
            
            if attendance_status == 'present':
                attendance.mark_present()
                attendance.marked_by_host_at = datetime.utcnow()
                marked_count += 1
            elif attendance_status == 'absent':
                attendance.status = 'absent'
        
        if workshop.status != 'completed':
            workshop.status = 'completed'
            
        db.session.commit()
        
        # Send feedback notifications to present students
        from app.models.notification import Notification
        
        for registration in registrations:
            attendance_status = request.form.get(f'attendance_{registration.user_id}')
            if attendance_status == 'present':
                # Quick check if already notified
                existing_notif = Notification.query.filter_by(
                    user_id=registration.user_id,
                    notification_type='feedback',
                    subject=f'Feedback Requested: {workshop.title}'
                ).first()
                
                if not existing_notif:
                    # Notify them!
                    notification = Notification(
                        user_id=registration.user_id,
                        notification_type='feedback',
                        subject=f'Feedback Requested: {workshop.title}',
                        message=f'Thank you for attending "{workshop.title}"! Please take a moment to submit your feedback on the workshop details page.',
                        email_sent=False
                    )
                    db.session.add(notification)
        
        db.session.commit()
        flash(f'Attendance marked for {marked_count} student(s) and workshop marked as completed.', 'success')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # GET request - show attendance form
    return render_template('attendance/manage.html', 
                         workshop=workshop, 
                         registrations=registrations)


@attendance_bp.route('/workshops/<int:id>/feedback', methods=['GET', 'POST'])
@login_required
def submit_feedback(id):
    """Student submits feedback for a completed workshop"""
    workshop = Workshop.query.get_or_404(id)
    
    # Check if workshop is completed
    if workshop.status != 'completed':
        flash('You can only submit feedback for completed workshops.', 'warning')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Check if user attended the workshop (marked as present)
    attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        workshop_id=workshop.id,
        status='present'
    ).first()
    
    if not attendance:
        flash('You must attend this workshop to submit feedback.', 'warning')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Check if already submitted feedback
    existing_feedback = Feedback.query.filter_by(
        user_id=current_user.id,
        workshop_id=workshop.id
    ).first()
    
    if existing_feedback:
        flash('You have already submitted feedback for this workshop.', 'info')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    form = FeedbackForm()
    
    if form.validate_on_submit():
        # Create feedback record
        feedback = Feedback(
            user_id=current_user.id,
            workshop_id=workshop.id,
            rating=int(form.rating.data),
            comment=form.comment.data.strip() if form.comment.data else None
        )
        db.session.add(feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    return render_template('feedback/submit.html', 
                         workshop=workshop, 
                         form=form)


@attendance_bp.route('/workshops/<int:id>/feedback/view')
@login_required
def view_workshop_feedback(id):
    """Host views aggregated feedback for their workshop"""
    workshop = Workshop.query.get_or_404(id)
    
    # Check if user is the host or admin
    if not current_user.is_admin() and current_user.id != workshop.host_id:
        flash('You do not have permission to view feedback for this workshop.', 'danger')
        return redirect(url_for('workshop.view_workshop', id=id))
    
    # Get all feedback for this workshop
    feedback_list = Feedback.query.filter_by(workshop_id=workshop.id).all()
    
    # Calculate statistics
    total_feedback = len(feedback_list)
    average_rating = 0
    if total_feedback > 0:
        average_rating = sum(f.rating for f in feedback_list) / total_feedback
    
    # Rating distribution
    rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for feedback in feedback_list:
        rating_distribution[feedback.rating] += 1
    
    return render_template('feedback/view.html',
                         workshop=workshop,
                         feedback_list=feedback_list,
                         total_feedback=total_feedback,
                         average_rating=round(average_rating, 2),
                         rating_distribution=rating_distribution)


@attendance_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with analytics and statistics"""
    # Check if admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Total workshops
    total_workshops = Workshop.query.count()
    
    # Workshops by status
    scheduled_workshops = Workshop.query.filter_by(status='scheduled').count()
    completed_workshops = Workshop.query.filter_by(status='completed').count()
    cancelled_workshops = Workshop.query.filter_by(status='cancelled').count()
    
    # Total users
    total_users = User.query.count()
    total_students = User.query.filter(User.role == 'student').count()
    total_hosts = User.query.filter(User.role == 'host').count()
    approved_hosts = User.query.filter_by(role='host', is_approved_host=True).count()
    
    # Total registrations
    total_registrations = Registration.query.count()
    confirmed_registrations = Registration.query.filter_by(status='confirmed').count()
    
    # Attendance rate (percentage of confirmed attendees who attended)
    total_attendance = Attendance.query.filter_by(status='present').count()
    attendance_rate = 0
    if confirmed_registrations > 0:
        attendance_rate = (total_attendance / confirmed_registrations) * 100
    
    # Popular categories (top 5)
    category_stats = db.session.query(
        Workshop.category,
        func.count(Workshop.id).label('workshop_count'),
        func.avg(Feedback.rating).label('avg_rating')
    ).outerjoin(Feedback).group_by(Workshop.category).order_by(
        func.count(Workshop.id).desc()
    ).limit(5).all()
    
    # Active hosts (by number of workshops hosted)
    active_hosts = db.session.query(
        User.id,
        User.full_name,
        User.student_number,
        func.count(Workshop.id).label('workshop_count')
    ).join(Workshop).filter(
        User.role == 'host'
    ).group_by(User.id).order_by(
        func.count(Workshop.id).desc()
    ).limit(10).all()
    
    # Recent workshops
    recent_workshops = Workshop.query.order_by(Workshop.created_at.desc()).limit(10).all()
    
    # Feedback statistics
    total_feedback = Feedback.query.count()
    avg_overall_rating = 0
    if total_feedback > 0:
        avg_overall_rating = db.session.query(func.avg(Feedback.rating)).scalar() or 0
    
    return render_template('admin/dashboard.html',
                         total_workshops=total_workshops,
                         scheduled_workshops=scheduled_workshops,
                         completed_workshops=completed_workshops,
                         cancelled_workshops=cancelled_workshops,
                         total_users=total_users,
                         total_students=total_students,
                         total_hosts=total_hosts,
                         approved_hosts=approved_hosts,
                         total_registrations=total_registrations,
                         confirmed_registrations=confirmed_registrations,
                         total_attendance=total_attendance,
                         attendance_rate=round(attendance_rate, 2),
                         category_stats=category_stats,
                         active_hosts=active_hosts,
                         recent_workshops=recent_workshops,
                         total_feedback=total_feedback,
                         avg_overall_rating=round(avg_overall_rating, 2))


@attendance_bp.route('/admin/export/csv')
@login_required
def export_csv():
    """Export participation and attendance data as CSV"""
    # Check if admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get all workshops with attendance data
    workshops = Workshop.query.order_by(Workshop.date_time.desc()).all()
    
    # Create CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Workshop ID',
        'Title',
        'Category',
        'Date & Time',
        'Host',
        'Capacity',
        'Registered',
        'Attended',
        'Attendance Rate',
        'Avg Rating',
        'Total Feedback'
    ])
    
    # Write data for each workshop
    for workshop in workshops:
        # Count attendance
        attended = Attendance.query.filter_by(
            workshop_id=workshop.id,
            status='present'
        ).count()
        
        # Calculate attendance rate
        attendance_rate = 0
        if workshop.registered_count > 0:
            attendance_rate = round((attended / workshop.registered_count) * 100, 2)
        
        # Get feedback stats
        workshop_feedback = Feedback.query.filter_by(workshop_id=workshop.id).all()
        total_feedback = len(workshop_feedback)
        avg_rating = 0
        if total_feedback > 0:
            avg_rating = round(sum(f.rating for f in workshop_feedback) / total_feedback, 2)
        
        writer.writerow([
            workshop.id,
            workshop.title,
            workshop.category,
            workshop.date_time.strftime('%Y-%m-%d %H:%M'),
            workshop.host.full_name or workshop.host.student_number,
            workshop.capacity,
            workshop.registered_count,
            attended,
            f'{attendance_rate}%',
            avg_rating,
            total_feedback
        ])
    
    # Prepare response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'workshop_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@attendance_bp.route('/admin/export/pdf')
@login_required
def export_pdf():
    """Export participation and attendance data as PDF"""
    # Check if admin
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # For now, redirect to CSV with a note
    # In production, use reportlab or weasyprint for PDF generation
    flash('PDF export coming soon. Using CSV export instead.', 'info')
    return redirect(url_for('attendance.export_csv'))


@attendance_bp.route('/api/attendance-trends')
@login_required
def get_attendance_trends():
    """Get attendance trends data for Chart.js"""
    # Check if admin
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get last 12 months attendance data
    today = datetime.utcnow()
    months_data = []
    
    for i in range(11, -1, -1):
        month_date = today - timedelta(days=30*i)
        year = month_date.year
        month = month_date.month
        
        # Count workshops and attendance for this month
        workshops = Workshop.query.filter(
            extract('year', Workshop.date_time) == year,
            extract('month', Workshop.date_time) == month
        ).all()
        
        workshop_ids = [w.id for w in workshops]
        attended = Attendance.query.filter(
            Attendance.workshop_id.in_(workshop_ids),
            Attendance.status == 'present'
        ).count() if workshop_ids else 0
        
        months_data.append({
            'month': month_date.strftime('%b %Y'),
            'workshops': len(workshops),
            'attended': attended
        })
    
    return jsonify(months_data)


@attendance_bp.route('/api/category-popularity')
@login_required
def get_category_popularity():
    """Get category popularity data for Chart.js"""
    # Check if admin
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get category statistics
    category_stats = db.session.query(
        Workshop.category,
        func.count(Workshop.id).label('workshop_count'),
        func.avg(Feedback.rating).label('avg_rating')
    ).outerjoin(Feedback).group_by(Workshop.category).all()
    
    result = []
    for stat in category_stats:
        result.append({
            'category': stat.category,
            'workshops': stat.workshop_count,
            'avg_rating': round(stat.avg_rating, 2) if stat.avg_rating else 0
        })
    
    return jsonify(result)


@attendance_bp.route('/api/rating-distribution')
@login_required
def get_rating_distribution():
    """Get rating distribution data for Chart.js"""
    # Check if admin
    if not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get rating distribution
    rating_dist = db.session.query(
        Feedback.rating,
        func.count(Feedback.id).label('count')
    ).group_by(Feedback.rating).all()
    
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rating, count in rating_dist:
        distribution[rating] = count
    
    return jsonify({
        'labels': ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
        'data': [distribution[1], distribution[2], distribution[3], distribution[4], distribution[5]]
    })
