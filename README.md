# SecOpsHub

A Security Operations Center (SOC) web app for case management, evidence tracking, and incident response playbooks. Built with Flask and MySQL.

## Features

- Dashboard with live case stats and Chart.js visualizations
- Case management with severity levels and status workflow
- Evidence tracking with chain-of-custody logging
- Standardized incident response playbooks
- Built-in tools: IP intelligence, port scanner, password analyzer, CVE feed, email header analyzer, hash identifier
- Role-based access (Analyst / Lead)
- Full activity audit log

## Tech stack

Python 3.13, Flask 3.0, MySQL (PyMySQL), bcrypt, Flask-Login, Flask-WTF, Chart.js, Jinja2. Tested with pytest.

## Setup

```bash
git clone https://github.com/prajwal087/Web-Coursework.git
cd SecOpsHub
pip install -r requirements.txt
```

Create a `.env` file:

```env
FLASK_SECRET_KEY=generate-a-random-secret-key
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=secops_hub
FLASK_DEBUG=True
```

Then run:

```bash
python run.py
```

Open `http://127.0.0.1:5000` and register your first account. Tables are created automatically on first run.

## Security

bcrypt password hashing, CSRF protection, rate limiting, security headers (CSP, X-Frame-Options, etc.), session fingerprinting, account lockout, and parameterized queries throughout.

## Testing

```bash
pytest tests/ -v
```

## License

MIT.

