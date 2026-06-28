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


@tools_bp.route('/port-scan', methods=['POST'])
@login_required
def port_scan():
    host = request.form['host'].strip()
    if _is_private_host(host):
        flash('Scanning internal or private IP addresses is not allowed', 'error')
        return redirect(url_for('tools.index'))
    ports = request.form.get('ports', '22,80,443,3389,8080')
    case_id = request.form.get('case_id')
    port_list = [int(p.strip()) for p in ports.split(',') if p.strip().isdigit()]
    results = []
    for port in port_list:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            code = sock.connect_ex((host, port))
            results.append({'port': port, 'open': code == 0})
        except socket.gaierror:
            results.append({'port': port, 'open': False, 'error': 'Address resolution failed'})
        except OSError as e:
            results.append({'port': port, 'open': False, 'error': str(e)})
        finally:
            sock.close()
    return render_template('tools/port_scan.html',
                           host=host,
                           results=results,
                           case_id=case_id)


@tools_bp.route('/password', methods=['POST'])
@login_required
def password_analyzer():
    password = request.form['password']
    case_id = request.form.get('case_id')
    length = len(password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    score = 0
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1
    if has_upper:
        score += 1
    if has_lower:
        score += 1
    if has_digit:
        score += 1
    if has_special:
        score += 1
    if score <= 2:
        strength = 'Weak'
    elif score <= 4:
        strength = 'Moderate'
    elif score <= 6:
        strength = 'Strong'
    else:
        strength = 'Very Strong'
    analysis = {
        'length': length,
        'has_upper': has_upper,
        'has_lower': has_lower,
        'has_digit': has_digit,
        'has_special': has_special,
        'score': score,
        'strength': strength,
    }
    return render_template('tools/password.html',
                           analysis=analysis,
                           case_id=case_id)


@tools_bp.route('/cve-feed', methods=['POST'])
@login_required
def cve_feed():
    keyword = request.form.get('keyword', '')
    case_id = request.form.get('case_id')
    try:
        url = 'https://services.nvd.nist.gov/rest/json/cves/2.0'
        params = {'resultsPerPage': 10}
        if keyword:
            params['keywordSearch'] = keyword
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        vulnerabilities = data.get('vulnerabilities', [])
    except requests.exceptions.Timeout:
        return render_template('tools/cve_feed.html',
                               vulnerabilities=[], error='Request timed out',
                               keyword=keyword, case_id=case_id)
    except requests.exceptions.ConnectionError:
        return render_template('tools/cve_feed.html',
                               vulnerabilities=[], error='Failed to connect to NVD',
                               keyword=keyword, case_id=case_id)
    except (ValueError, KeyError):
        return render_template('tools/cve_feed.html',
                               vulnerabilities=[], error='Invalid response from NVD',
                               keyword=keyword, case_id=case_id)
    return render_template('tools/cve_feed.html',
                           vulnerabilities=vulnerabilities,
                           keyword=keyword,
                           case_id=case_id)


@tools_bp.route('/save-evidence', methods=['POST'])
@login_required
def save_evidence():
    case_id = request.form.get('case_id')
    source = request.form.get('source', 'manual')
    content = request.form.get('content', '')
    title = request.form.get('title', f'Evidence from {source}')
    if not case_id:
        flash('No case selected', 'error')
        return redirect(url_for('tools.index'))
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO evidence (title, content, source, case_id) VALUES (%s, %s, %s, %s)",
                (title, content, source, case_id)
            )
        conn.commit()
        flash('Evidence saved to case', 'success')
    finally:
        conn.close()
    return redirect(url_for('cases.view', id=case_id))



