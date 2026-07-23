from flask import Blueprint, render_template
from flask_login import login_required
from app.services import DashboardService

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')


@dashboard_bp.route('/')
@login_required
def index():
    stats = DashboardService.get_stats()
    return render_template('dashboard/index.html', **stats)
