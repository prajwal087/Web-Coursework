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
