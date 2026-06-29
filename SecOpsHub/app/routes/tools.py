import ipaddress
import socket

import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services import EvidenceService

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
    cases = EvidenceService.get_all_cases_basic()
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


@tools_bp.route('/email-header-analyzer', methods=['POST'])
@login_required
def email_header_analyzer():
    raw = request.form.get('headers', '')
    case_id = request.form.get('case_id')
    result = {}
    for line in raw.splitlines():
        line = line.strip()
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip().lower()
        val = val.strip()
        if key in ('from', 'to', 'subject', 'date', 'message-id', 'return-path'):
            result[key] = val
        if key == 'authentication-results':
            spf = dkim = dmarc = None
            for part in val.replace(';', ' ').split():
                part = part.strip()
                if part.startswith('spf='):
                    spf = part.split('=')[1]
                elif part.startswith('dkim='):
                    dkim = part.split('=')[1]
                elif part.startswith('dmarc='):
                    dmarc = part.split('=')[1]
            result['spf'] = spf or 'neutral'
            result['dkim'] = dkim or 'neutral'
            result['dmarc'] = dmarc or 'neutral'
    received_headers = []
    for line in raw.splitlines():
        if line.strip().lower().startswith('received:'):
            received_headers.append(line.strip())
    result['received_count'] = len(received_headers)
    result['received_headers'] = received_headers[:10]
    return render_template('tools/email_header.html',
                           result=result,
                           case_id=case_id)


@tools_bp.route('/hash-identifier', methods=['POST'])
@login_required
def hash_identifier():
    raw_hash = request.form.get('hash', '').strip()
    case_id = request.form.get('case_id')
    h = raw_hash.replace(' ', '')
    length = len(h)
    is_hex = all(c in '0123456789abcdefABCDEF' for c in h)
    prefix = h.split('$')[0] if '$' in h else ''
    candidates = []

    if is_hex:
        candidates.append(('CRC-32', 8, 6))
        candidates.append(('CRC-32B', 8, 6))
        candidates.append(('ADLER-32', 8, 6))
        candidates.append(('MD5', 32, 4))
        candidates.append(('SHA-1', 40, 6))
        candidates.append(('SHA-256', 64, 8))
        candidates.append(('SHA-384', 96, 12))
        candidates.append(('SHA-512', 128, 16))
        candidates.append(('SHA-512/256', 64, 8))
        candidates.append(('SHA3-256', 64, 8))
        candidates.append(('SHA3-512', 128, 16))
        candidates.append(('BLAKE2b-256', 64, 8))
        candidates.append(('BLAKE2b-512', 128, 16))
        candidates.append(('RIPEMD-160', 40, 6))
        candidates.append(('Whirlpool', 128, 16))
        candidates.append(('NTLM', 32, 4))
        candidates.append(('LM', 32, 4))
        candidates.append(('MySQL 5.x', 41, 5))
        candidates.append(('SHA-256 (Unix)', 64, 8))
        candidates.append(('Snefru-256', 64, 8))
        candidates.append(('GOST R 34.11-94', 64, 8))
        matching = [(name, l, s) for name, l, s in candidates if l == length]
        matching.sort(key=lambda x: -x[2])
        result = {
            'hash': raw_hash,
            'length': length,
            'is_hex': True,
            'possible_types': [name for name, l, s in matching] if matching else ['Unknown']
        }
    elif raw_hash.startswith('$2y$') or raw_hash.startswith('$2b$') or raw_hash.startswith('$2a$'):
        result = {
            'hash': raw_hash[:30] + '...' if len(raw_hash) > 30 else raw_hash,
            'length': length,
            'is_hex': False,
            'possible_types': ['bcrypt $2*$']
        }
    elif raw_hash.startswith('$argon2'):
        result = {
            'hash': raw_hash[:30] + '...' if len(raw_hash) > 30 else raw_hash,
            'length': length,
            'is_hex': False,
            'possible_types': ['Argon2']
        }
    elif len(h) == 16 and not is_hex:
        result = {
            'hash': raw_hash,
            'length': length,
            'is_hex': False,
            'possible_types': ['MySQL < 4.1', 'DES (Unix)']
        }
    else:
        result = {
            'hash': raw_hash,
            'length': length,
            'is_hex': False,
            'possible_types': ['Unknown format']
        }
    return render_template('tools/hash_identifier.html',
                           result=result,
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
    try:
        EvidenceService.add_evidence(case_id, title, content, source)
        flash('Evidence saved to case', 'success')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error saving evidence from tools: {str(e)}")
        flash('An error occurred while saving evidence', 'error')
    return redirect(url_for('cases.view', id=case_id))
