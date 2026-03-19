from flask import Blueprint, render_template
from app.models.user import User
from datetime import datetime

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page route"""
    return render_template('index.html')


@main_bp.route('/about')
def about():
    """About page route"""
    return render_template('about.html')


@main_bp.route('/privacy')
def privacy_policy():
    """Privacy Policy page - POPIA compliance"""
    return render_template('privacy_policy.html')


@main_bp.route('/hosts')
def hosts_directory():
    """Public directory of all approved hosts"""
    # Get all approved hosts with their workshops
    hosts = User.query.filter_by(role='host', approved_host=True).all()
    
    # Calculate statistics for each host
    host_data = []
    for host in hosts:
        upcoming_workshops = [w for w in host.hosted_workshops if w.date_time > datetime.utcnow() and w.status == 'scheduled']
        past_workshops = [w for w in host.hosted_workshops if w.date_time <= datetime.utcnow() or w.status != 'scheduled']
        
        host_data.append({
            'host': host,
            'upcoming_count': len(upcoming_workshops),
            'past_count': len(past_workshops),
            'total_participants': sum(w.registered_count for w in host.hosted_workshops)
        })
    
    # Sort by most active (most upcoming workshops first)
    host_data.sort(key=lambda x: x['upcoming_count'], reverse=True)
    
    return render_template('hosts.html', host_data=host_data)
