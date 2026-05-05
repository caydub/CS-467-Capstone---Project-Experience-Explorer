import functools
import hashlib
import os
import random
import xml.etree.ElementTree as ET

import pymysql
import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

# Load variables from .env file into the environment (local development only)
load_dotenv()

app = Flask(__name__)

IS_PROD = os.environ.get('GAE_ENV', '').startswith('standard')

# ------------------------------ Secrets ------------------------------ #


def get_secret(secret_id):
    """Fetch a secret value from GCP Secret Manager.

    Used when running on App Engine to avoid storing passwords in code or config files.
    """
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/project-experience-explorer/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


if IS_PROD:
    db_password = get_secret('db_flask_user_password')
    app.secret_key = get_secret('flask_secret_key')
else:
    db_password = os.environ.get('DB_PASSWORD')
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-not-for-production')

# ------------------------------ Database ------------------------------ #

db_config = {
    'user': 'flask_user',
    'password': db_password,
    'database': 'project_explorer_db',
    'cursorclass': pymysql.cursors.DictCursor
}

if IS_PROD:
    db_config['unix_socket'] = (
        '/cloudsql/project-experience-explorer:us-central1:'
        'project-experience-explorer-db'
    )
else:
    db_config['host'] = '127.0.0.1'

# ------------------------------ CAS Config ------------------------------ #

CAS_BASE = 'https://login.oregonstate.edu/cas'
CAS_LOGIN_URL = f'{CAS_BASE}/login'
CAS_LOGOUT_URL = f'{CAS_BASE}/logout'
CAS_VALIDATE_URL = f'{CAS_BASE}/serviceValidate'


def get_db_connection():
    """Open and return a new database connection."""
    return pymysql.connect(**db_config)


# ------------------------------ Auth Helpers ------------------------------ #

ADJECTIVES = [
    'Amber', 'Azure', 'Bold', 'Bright', 'Calm', 'Clever', 'Cobalt', 'Cool',
    'Crimson', 'Dark', 'Deep', 'Dusky', 'Eager', 'Faint', 'Fierce', 'Fluid',
    'Frost', 'Golden', 'Grand', 'Grey', 'Hidden', 'Honest', 'Humble',
    'Jade', 'Kind', 'Lofty', 'Lucky', 'Marble', 'Mellow', 'Misty', 'Noble',
    'Pale', 'Quiet', 'Rapid', 'Rustic', 'Silent', 'Silver', 'Solar', 'Stark',
    'Storm', 'Swift', 'Teal', 'Velvet', 'Vivid', 'Warm', 'Wild',
    'Windy', 'Ivory', 'Zeal',
]

NOUNS = [
    'Bark', 'Bear', 'Birch', 'Branch', 'Brook', 'Cedar', 'Cliff', 'Cloud',
    'Crane', 'Creek', 'Deer', 'Elm', 'Falcon', 'Fern', 'Field', 'Finch',
    'Fox', 'Glen', 'Grove', 'Hawk', 'Heath', 'Heron', 'Hollow', 'Lark',
    'Leaf', 'Maple', 'Meadow', 'Mist', 'Moss', 'Moth', 'Oak', 'Peak',
    'Pine', 'Rain', 'Raven', 'Reed', 'Ridge', 'River', 'Robin', 'Root',
    'Shore', 'Snow', 'Sparrow', 'Stone', 'Tide', 'Vale', 'Willow', 'Wind',
    'Wolf', 'Wren',
]


def generate_unique_pseudonym(cursor):
    """Generate an adjective+noun+number pseudonym that does not already exist in the students table."""
    while True:
        candidate = random.choice(ADJECTIVES) + random.choice(NOUNS) + str(random.randint(1, 999))
        cursor.execute('SELECT 1 FROM students WHERE pseudonym = %s', (candidate,))
        if not cursor.fetchone():
            return candidate


def get_or_create_student(onid):
    """Look up a student by hashed ONID. Create a new record with a pseudonym if not found.

    Returns a dict with student_id and pseudonym.
    """
    # hash the ONID — we never store the raw username
    onid_hash = hashlib.sha256(onid.lower().encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT student_id, pseudonym FROM students WHERE onid_hash = %s',
        (onid_hash,)
    )
    student = cursor.fetchone()

    if not student:
        pseudonym = generate_unique_pseudonym(cursor)
        cursor.execute(
            'INSERT INTO students (onid_hash, pseudonym) VALUES (%s, %s)',
            (onid_hash, pseudonym)
        )
        conn.commit()
        student = {'student_id': cursor.lastrowid, 'pseudonym': pseudonym}

    conn.close()
    return student


def login_required(f):
    """Decorator — redirect to login if the user is not authenticated.

    Wrap any route that requires an ONID login with @login_required.
    Usage:
        @app.route('/some-protected-route')
        @login_required
        def protected_route():
            ...
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'student_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ------------------------------ Auth Routes ------------------------------ #


@app.route('/login')
def login():
    """Redirect to the OSU CAS login page."""
    service_url = url_for('auth_callback', _external=True)
    return redirect(f'{CAS_LOGIN_URL}?service={service_url}')


@app.route('/logout')
def logout():
    """Clear the session and redirect to the CAS logout page."""
    session.clear()
    service_url = url_for('home', _external=True)
    return redirect(f'{CAS_LOGOUT_URL}?service={service_url}')


@app.route('/auth/callback')
def auth_callback():
    """Handle the CAS callback after a successful login.

    CAS redirects here with a one-time ticket. We validate the ticket
    against the CAS server, extract the ONID, and create or retrieve
    the student record before setting the session.
    """
    ticket = request.args.get('ticket')
    if not ticket:
        # no ticket means something went wrong — just go home
        return redirect(url_for('home'))

    # validate the ticket with the CAS server
    service_url = url_for('auth_callback', _external=True)
    response = requests.get(CAS_VALIDATE_URL, params={
        'ticket': ticket,
        'service': service_url,
    })

    # parse the XML response from CAS
    root = ET.fromstring(response.text)
    ns = {'cas': 'http://www.yale.edu/tp/cas'}
    success = root.find('cas:authenticationSuccess', ns)

    if success is None:
        # ticket validation failed — send them back home
        return redirect(url_for('home'))

    onid = success.find('cas:user', ns).text.strip()

    # look up or create the student record
    student = get_or_create_student(onid)

    session['student_id'] = student['student_id']
    session['pseudonym'] = student['pseudonym']

    return redirect(url_for('home'))

# ------------------------------ Public Routes ------------------------------ #


@app.route('/')
def home():
    """Render the project listing page with optional search filtering."""
    search_query = request.args.get('search', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT
            p.project_id,
            p.title,
            p.description,
            COUNT(r.review_id) AS review_count,
            AVG(r.difficulty) AS difficulty,
            AVG(r.workload) AS workload,
            AVG(r.would_recommend) AS would_recommend,
            MAX(r.review_text) AS top_snippet
        FROM projects p
        LEFT JOIN reviews r ON p.project_id = r.project_id
    """

    if search_query:
        cursor.execute(base_query + 'WHERE p.title LIKE %s GROUP BY p.project_id ORDER BY p.title',
                       (f'%{search_query}%',))
    else:
        cursor.execute(base_query + 'GROUP BY p.project_id ORDER BY p.title')

    projects = cursor.fetchall()
    conn.close()

    return render_template(
        'index.html',
        projects=projects,
        search_query=search_query
    )


@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Render the project detail page with all reviews."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.project_id,
            p.title,
            p.description,
            AVG(r.difficulty) AS difficulty,
            AVG(r.workload) AS workload,
            AVG(r.would_recommend) AS would_recommend
        FROM projects p
        LEFT JOIN reviews r ON p.project_id = r.project_id
        WHERE p.project_id = %s
        GROUP BY p.project_id
    """, (project_id,))

    project = cursor.fetchone()

    if project is None:
        conn.close()
        return "Project not found", 404

    cursor.execute("""
        SELECT
            r.review_text,
            r.term,
            r.difficulty,
            r.workload,
            r.would_recommend,
            s.pseudonym
        FROM reviews r
        JOIN students s ON r.student_id = s.student_id
        WHERE r.project_id = %s
        ORDER BY r.created_at DESC
    """, (project_id,))

    reviews = cursor.fetchall()
    conn.close()

    return render_template(
        'project_detail.html',
        project=project,
        reviews=reviews
    )


@app.route('/project/<int:project_id>/submit-review')
@login_required
def submit_review(project_id):
    """Display the review submission page."""
    return render_template('submit_review.html', project_id=project_id)

# ------------------------------ Dev/Debug Routes ------------------------------ #


@app.route('/test-db')
def test_db():
    """Temporary route to verify the database connection is working.

    Remove this before final deployment.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        conn.close()
        return f'Database connection successful! Result: {result}'
    except Exception as e:
        return f'Database connection failed: {str(e)}'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
