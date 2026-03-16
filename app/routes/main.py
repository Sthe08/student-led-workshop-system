from flask import Blueprint, render_template

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
