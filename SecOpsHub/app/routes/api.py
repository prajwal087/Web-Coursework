from flask import Blueprint, jsonify
from flask_login import login_required
from app.services import CaseService, DashboardService, AnalystService

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/cases')
@login_required
def list_cases():
    rows, _, _, _ = CaseService.get_all_cases(page=1, per_page=100)
    return jsonify([{
        'id': r['id'],
        'title': r['title'],
        'severity': r['severity'],
        'status': r['status'],
        'analyst': r.get('username', ''),
        'created_at': str(r.get('created_at', ''))
    } for r in rows])


@api_bp.route('/cases/<int:id>')
@login_required
def get_case(id):
    case = CaseService.get_case_by_id(id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    return jsonify({
        'id': case.id,
        'title': case.title,
        'description': getattr(case, 'description', ''),
        'severity': case.severity,
        'status': case.status,
        'analyst': getattr(case, 'username', ''),
        'created_at': str(case.created_at or ''),
        'updated_at': str(case.updated_at or '')
    })


@api_bp.route('/stats')
@login_required
def stats():
    s = DashboardService.get_stats()
    return jsonify({
        'cases': s['total_cases'],
        'analysts': s['total_analysts'],
        'evidence': s['total_evidence'],
        'playbooks': s['total_playbooks'],
        'open_cases': s['open_cases'],
        'in_progress_cases': s['in_progress_cases'],
        'closed_cases': s['closed_cases'],
        'severity_counts': s['severity_counts']
    })


@api_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    s = DashboardService.get_stats()
    status_labels = ['Open', 'In Progress', 'Closed']
    status_data = [s['open_cases'], s['in_progress_cases'], s['closed_cases']]
    sev_labels = ['Low', 'Medium', 'High', 'Critical']
    sev_data = [s['severity_counts']['low'], s['severity_counts']['medium'], s['severity_counts']['high'], s['severity_counts']['critical']]
    return jsonify({
        'status_chart': {'labels': status_labels, 'data': status_data},
        'severity_chart': {'labels': sev_labels, 'data': sev_data}
    })


@api_bp.route('/analysts')
@login_required
def list_analysts():
    analysts = AnalystService.get_all_analysts()
    return jsonify([{
        'id': a.id,
        'username': a.username,
        'email': a.email,
        'role': a.role,
        'created_at': str(a.created_at or '')
    } for a in analysts])
