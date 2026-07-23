from flask import Blueprint, render_template
from flask_login import login_required
from app.services import AdminService
from app import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@role_required('lead')
def index():
    stats = AdminService.get_admin_stats()
    return render_template('admin/index.html', **stats)
