import functools
import hashlib
import os
import random

import pymysql
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

load_dotenv()

app = Flask(__name__)

IS_PROD = os.environ.get('GAE_ENV', '').startswith('standard')


# ------------------------------ Secrets ------------------------------ #

def get_secret(secret_id):
    """Fetch a secret value from GCP Secret Manager."""
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/project-experience-explorer/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


if IS_PROD:
    db_password = get_secret('db_flask_user_password')
    app.secret_key = get_secret('flask_secret_key')
    google_client_id = get_secret('google_client_id')
    google_client_secret = get_secret('google_client_secret')
else:
    db_password = os.environ.get('DB_PASSWORD')
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-not-for-production')
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')

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

# ------------------------------ Google OAuth Config ------------------------------ #

oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=google_client_id,
    client_secret=google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# ------------------------------ Database Helpers ------------------------------ #


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
    """Generate a unique pseudonym that does not already exist."""
    while True:
        candidate = (
            random.choice(ADJECTIVES)
            + random.choice(NOUNS)
            + str(random.randint(1, 999))
        )
        cursor.execute(
            'SELECT 1 FROM students WHERE pseudonym = %s',
            (candidate,)
        )
        if not cursor.fetchone():
            return candidate


def get_or_create_student(email):
    """Look up a student by hashed email. Create a new record with a pseudonym if not found.

    Returns a dict with student_id and pseudonym.
    """
    # hash the email -- we never store the raw address
    email_hash = hashlib.sha256(email.lower().encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT student_id, pseudonym FROM students WHERE onid_hash = %s',
        (email_hash,)
    )
    student = cursor.fetchone()

    if not student:
        pseudonym = generate_unique_pseudonym(cursor)
        cursor.execute(
            'INSERT INTO students (onid_hash, pseudonym) VALUES (%s, %s)',
            (email_hash, pseudonym)
        )
        conn.commit()
        student = {'student_id': cursor.lastrowid, 'pseudonym': pseudonym}

    conn.close()
    return student


def login_required(f):
    """Redirect to login if the user is not authenticated."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'student_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated


# ------------------------------ Auth Routes ------------------------------ #

@app.route('/login')
def login():
    """Redirect to Google OAuth login."""
    redirect_uri = url_for('auth_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/logout')
def logout():
    """Clear the session and redirect to homepage."""
    session.clear()
    return redirect(url_for('home'))


@app.route('/auth/callback')
def auth_callback():
    """Handle the Google OAuth callback after a successful login.

    Verifies the user has an @oregonstate.edu email, then creates or
    retrieves their student record and sets the session.
    """
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token, nonce=session.get('nonce'))
    email = user_info.get('email', '')

    # enforce OSU-only access
    if not email.endswith('@oregonstate.edu'):
        return 'Access restricted to OSU students only.', 403

    student = get_or_create_student(email)

    session['student_id'] = student['student_id']
    session['pseudonym'] = student['pseudonym']

    return redirect(url_for('home'))


# ------------------------------ Public Routes ------------------------------ #

@app.route('/')
def home():
    """Render the project listing page with optional search, filter, and sort."""
    search_query = request.args.get('search', '').strip()
    sort_option = request.args.get('sort', 'title')

    def parse_rating_filter(param):
        """Return int 1-5 if the query param is a valid rating, else None."""
        try:
            val = int(request.args.get(param, 0))
            return val if 1 <= val <= 5 else None
        except (ValueError, TypeError):
            return None

    filter_min_difficulty = parse_rating_filter('min_difficulty')
    filter_min_workload = parse_rating_filter('min_workload')
    filter_min_recommend = parse_rating_filter('min_recommend')
    filter_has_reviews = request.args.get('has_reviews') == '1'

    sort_options = {
        'title': 'p.title ASC',
        'most_reviews': 'review_count DESC, p.title ASC',
        'avg_score': 'avg_score DESC, p.title ASC',
        'highest_recommendation': 'avg_recommend DESC, p.title ASC',
        'highest_difficulty': 'avg_difficulty DESC, p.title ASC',
        'highest_workload': 'avg_workload DESC, p.title ASC',
    }
    order_by = sort_options.get(sort_option, sort_options['title'])

    where_clauses = []
    where_params = []
    having_clauses = []
    having_params = []

    if search_query:
        where_clauses.append('p.title LIKE %s')
        where_params.append(f'%{search_query}%')

    if filter_min_difficulty:
        having_clauses.append('AVG(r.difficulty) >= %s')
        having_params.append(filter_min_difficulty)

    if filter_min_workload:
        having_clauses.append('AVG(r.workload) >= %s')
        having_params.append(filter_min_workload)

    if filter_min_recommend:
        having_clauses.append('AVG(r.would_recommend) >= %s')
        having_params.append(filter_min_recommend)

    if filter_has_reviews:
        having_clauses.append('COUNT(r.review_id) > 0')

    where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''
    having_sql = ('HAVING ' + ' AND '.join(having_clauses)) if having_clauses else ''

    query = f"""
        SELECT
            p.project_id,
            p.title,
            COUNT(r.review_id)                                                  AS review_count,
            AVG(r.difficulty)                                                   AS avg_difficulty,
            AVG(r.workload)                                                     AS avg_workload,
            AVG(r.would_recommend)                                              AS avg_recommend,
            (AVG(r.difficulty) + AVG(r.workload)
                + AVG(r.team_dynamics) + AVG(r.would_recommend)) / 4.0         AS avg_score,
            MAX(r.review_text)                                                  AS top_snippet
        FROM projects p
        LEFT JOIN reviews r ON p.project_id = r.project_id
        {where_sql}
        GROUP BY p.project_id
        {having_sql}
        ORDER BY {order_by}
    """

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, where_params + having_params)
    projects = cursor.fetchall()
    conn.close()

    return render_template(
        'index.html',
        projects=projects,
        search_query=search_query,
        sort_option=sort_option,
        filter_min_difficulty=filter_min_difficulty,
        filter_min_workload=filter_min_workload,
        filter_min_recommend=filter_min_recommend,
        filter_has_reviews=filter_has_reviews,
    )


@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Render the project detail page with all reviews and comments."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.project_id,
            p.title,
            p.description,
            AVG(r.difficulty) AS difficulty,
            AVG(r.workload) AS workload,
            AVG(r.team_dynamics) AS team_dynamics,
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
            r.review_id,
            r.review_text,
            r.term,
            r.difficulty,
            r.workload,
            r.team_dynamics,
            r.would_recommend,
            s.pseudonym,
            (SELECT COUNT(*) FROM helpfulness h
             WHERE h.review_id = r.review_id AND h.value = 1)  AS helpful_count,
            (SELECT COUNT(*) FROM helpfulness h
             WHERE h.review_id = r.review_id AND h.value = -1) AS not_helpful_count
        FROM reviews r
        JOIN students s ON r.student_id = s.student_id
        WHERE r.project_id = %s
        ORDER BY r.created_at DESC
    """, (project_id,))

    reviews = cursor.fetchall()

    # build a {review_id: vote_value} map for the logged-in user
    user_votes = {}
    if 'student_id' in session and reviews:
        review_ids = [r['review_id'] for r in reviews]
        placeholders = ', '.join(['%s'] * len(review_ids))
        cursor.execute(
            f'SELECT review_id, value FROM helpfulness'
            f' WHERE student_id = %s AND review_id IN ({placeholders})',
            [session['student_id']] + review_ids
        )
        user_votes = {row['review_id']: row['value'] for row in cursor.fetchall()}

    cursor.execute("""
        SELECT
            c.comment_id,
            c.review_id,
            c.comment_text,
            c.created_at,
            s.pseudonym
        FROM comments c
        JOIN students s ON c.student_id = s.student_id
        JOIN reviews r ON c.review_id = r.review_id
        WHERE r.project_id = %s
        ORDER BY c.created_at ASC
    """, (project_id,))

    comments = cursor.fetchall()

    conn.close()

    return render_template(
        'project_detail.html',
        project=project,
        reviews=reviews,
        comments=comments,
        user_votes=user_votes,
    )


@app.route('/project/<int:project_id>/submit-review', methods=['GET', 'POST'])
@login_required
def submit_review(project_id):
    """Display and process the review submission page."""
    if request.method == 'POST':
        term = request.form.get('term')

        try:
            difficulty = int(request.form.get('difficulty'))
            workload = int(request.form.get('workload'))
            team_dynamics = int(request.form.get('team_dynamics'))
            would_recommend = int(request.form.get('would_recommend'))

            ratings = [
                difficulty,
                workload,
                team_dynamics,
                would_recommend
            ]

            if not all(1 <= rating <= 5 for rating in ratings):
                return 'Ratings must be between 1 and 5', 400

        except (TypeError, ValueError):
            return 'Invalid rating value', 400

        review_text = request.form.get('review_text')

        conn = get_db_connection()

        try:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO reviews
                    (project_id, student_id, term, difficulty, workload,
                     team_dynamics, would_recommend, review_text)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                project_id,
                session['student_id'],
                term,
                difficulty,
                workload,
                team_dynamics,
                would_recommend,
                review_text
            ))

            conn.commit()

        finally:
            conn.close()

        return redirect(url_for('project_detail', project_id=project_id))

    return render_template('submit_review.html', project_id=project_id)


@app.route('/review/<int:review_id>/comment', methods=['POST'])
@login_required
def submit_comment(review_id):
    """Process a new comment submitted on a review."""
    comment_text = request.form.get('comment_text', '').strip()
    project_id = request.form.get('project_id')

    if not comment_text:
        return 'Comment cannot be empty', 400

    conn = get_db_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO comments
                (review_id, student_id, comment_text)
            VALUES
                (%s, %s, %s)
        """, (
            review_id,
            session['student_id'],
            comment_text
        ))

        conn.commit()

    finally:
        conn.close()

    return redirect(url_for('project_detail', project_id=project_id))


@app.route('/review/<int:review_id>/vote', methods=['POST'])
@login_required
def vote_review(review_id):
    """Toggle a helpful (1) or not-helpful (-1) vote on a review.

    Submitting the same vote twice removes it; submitting the opposite flips it.
    """
    raw_value = request.form.get('value')
    project_id = request.form.get('project_id')

    if raw_value not in ('1', '-1'):
        return 'Invalid vote value', 400

    value = int(raw_value)
    student_id = session['student_id']

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT value FROM helpfulness WHERE review_id = %s AND student_id = %s',
            (review_id, student_id)
        )
        existing = cursor.fetchone()

        if existing:
            if existing['value'] == value:
                # same vote — remove it (toggle off)
                cursor.execute(
                    'DELETE FROM helpfulness WHERE review_id = %s AND student_id = %s',
                    (review_id, student_id)
                )
            else:
                # opposite vote — flip it
                cursor.execute(
                    'UPDATE helpfulness SET value = %s WHERE review_id = %s AND student_id = %s',
                    (value, review_id, student_id)
                )
        else:
            cursor.execute(
                'INSERT INTO helpfulness (review_id, student_id, value) VALUES (%s, %s, %s)',
                (review_id, student_id, value)
            )

        conn.commit()
    finally:
        conn.close()

    return redirect(url_for('project_detail', project_id=project_id))


# ------------------------------ Dev/Debug Routes ------------------------------ #

@app.route('/test-db')
def test_db():
    """Temporary route to verify the database connection is working."""
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
