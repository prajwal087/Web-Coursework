from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from app.models.analyst import Analyst
from app.database import get_db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
