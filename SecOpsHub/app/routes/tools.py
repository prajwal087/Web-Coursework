import ipaddress
import socket

import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.evidence import Evidence
from app.models.case import Case
from app.database import get_db

tools_bp = Blueprint('tools', __name__, url_prefix='/tools')


_PRIVATE_RANGES = [
    '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
    '127.0.0.0/8', '169.254.0.0/16', '::1/128',
    'fc00::/7', 'fe80::/10'
]


def _is_private_host(host):
    try:
        ip = ipaddress.ip_address(host)
        return any(ip in ipaddress.ip_network(r, strict=False) for r in _PRIVATE_RANGES)
    except ValueError:
        return False


@tools_bp.route('/')
@login_required
def index():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM cases")
            cases = [Case.from_row(r) for r in cur.fetchall()]
    finally:
        conn.close()
    return render_template('tools/index.html', cases=cases)


@tools_bp.route('/ip-intel', methods=['POST'])
@login_required
def ip_intel():
    ip = request.form['ip']
    case_id = request.form.get('case_id')
    try:
        result = requests.get(f'https://ipinfo.io/{ip}/json', timeout=10).json()
    except requests.exceptions.Timeout:
        result = {'error': 'Request timed out'}
    except requests.exceptions.ConnectionError:
        result = {'error': 'Failed to connect to ipinfo.io'}
    except ValueError:
        result = {'error': 'Invalid response from ipinfo.io'}
    return render_template('tools/ip_intel.html',
                           result=result,
                           case_id=case_id,
                           ip=ip)


