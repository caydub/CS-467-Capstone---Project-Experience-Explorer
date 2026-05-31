import functools
import hashlib
import os
import random
import re
from datetime import datetime

import pymysql
from authlib.integrations.flask_client import OAuth
from bs4 import BeautifulSoup, NavigableString
from bs4 import Tag as BSTag
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from markupsafe import Markup, escape

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


# ------------------------------ Jinja2 Helpers ------------------------------ #


def rating_color(value):
    """Return a CSS hex color for a 1–5 rating value (red → green scale)."""
    if value is None:
        return '#ccc'
    if value < 1.5:
        return '#e74c3c'
    if value < 2.5:
        return '#e67e22'
    if value < 3.5:
        return '#f1c40f'
    if value < 4.5:
        return '#2ecc71'
    return '#27ae60'


def badge_color(pseudonym):
    """Return a consistent HSL background color derived from a pseudonym's first letter."""
    hue = (ord(pseudonym[0].upper()) * 137) % 360
    return f'hsl({hue}, 55%, 45%)'


def relative_time(dt):
    """Return a human-readable relative time string for a UTC datetime."""
    if dt is None:
        return ''
    diff = datetime.utcnow() - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return 'just now'
    if seconds < 3600:
        m = int(seconds / 60)
        return f'{m} minute{"s" if m != 1 else ""} ago'
    if seconds < 86400:
        h = int(seconds / 3600)
        return f'{h} hour{"s" if h != 1 else ""} ago'
    if seconds < 604800:
        d = int(seconds / 86400)
        return f'{d} day{"s" if d != 1 else ""} ago'
    if seconds < 2592000:
        w = int(seconds / 604800)
        return f'{w} week{"s" if w != 1 else ""} ago'
    return dt.strftime('%b %d, %Y')


app.jinja_env.globals['rating_color'] = rating_color
app.jinja_env.globals['badge_color'] = badge_color
app.jinja_env.filters['relative_time'] = relative_time

# ------------------------------ Description Formatter ------------------------------ #

# Detect HTML content produced by the new scraper (contains structural tags).
_HTML_RE = re.compile(r'<(?:h[3-5]|p|ul|ol|li|strong|em|br)\b', re.I)

# Known section-header words used by the legacy plain-text path.
_TOP_HEADERS = {
    'objectives', 'objective', 'motivations', 'motivation',
    'qualifications', 'qualification', 'background', 'technical background',
    'skills', 'required skills', 'desired skills', 'preferred skills',
    'overview', 'project overview', 'goals', 'goal',
    'deliverables', 'deliverable', 'requirements', 'requirement',
    'description', 'about', 'notes', 'note', 'summary',
    'features', 'feature', 'technologies', 'technology',
    'scope', 'responsibilities', 'resources', 'timeline',
    'details',
}


def _render_inline(node, parts):
    """Append an inline HTML fragment for a BS4 node to parts."""
    if isinstance(node, NavigableString):
        text = str(node)
        if text.strip():
            parts.append(str(escape(text)))
        elif text:
            parts.append(' ')
        return
    if not isinstance(node, BSTag):
        return
    name = node.name
    if name in ('strong', 'b'):
        t = node.get_text(strip=True)
        if t:
            parts.append(f'<strong>{escape(t)}</strong>')
    elif name in ('em', 'i'):
        t = node.get_text(strip=True)
        if t:
            parts.append(f'<em>{escape(t)}</em>')
    elif name == 'br':
        parts.append(' ')
    else:
        for child in node.children:
            _render_inline(child, parts)


def _is_section_header(text):
    """Return True if text is a known top-level section label."""
    return text.lower().rstrip(':') in _TOP_HEADERS


def _is_field_label(text):
    """Return True if text looks like a key-value label (short, ends with colon)."""
    return text.endswith(':') and len(text) <= 45 and not _is_section_header(text)


def _render_node(node, buf):
    """Recursively convert a BS4 node to controlled block-level HTML, appending to buf."""
    if isinstance(node, NavigableString):
        text = str(node).strip()
        if text:
            if _is_section_header(text):
                buf.append(f'<p class="desc-section"><strong>{escape(text.rstrip(":"))}</strong></p>')
            elif _is_field_label(text):
                buf.append(f'<p class="desc-label"><strong>{escape(text)}</strong></p>')
            else:
                buf.append(f'<p class="desc-para">{escape(text)}</p>')
        return
    if not isinstance(node, BSTag):
        return

    name = node.name

    if name in ('h3', 'h4', 'h5'):
        t = node.get_text(strip=True)
        if t:
            buf.append(f'<p class="desc-section"><strong>{escape(t)}</strong></p>')

    elif name == 'p':
        plain = node.get_text(strip=True)
        # Known section header
        if plain and _is_section_header(plain):
            buf.append(f'<p class="desc-section"><strong>{escape(plain.rstrip(":"))}</strong></p>')
            return
        # Field label (short text ending with colon, e.g. "Project Partner:")
        if plain and _is_field_label(plain):
            buf.append(f'<p class="desc-label"><strong>{escape(plain)}</strong></p>')
            return

        # A <p> may contain block children (ul/ol) interspersed with inline text.
        # Flush inline text as its own <p>, then recurse for block children.
        inline = []
        for child in node.children:
            if isinstance(child, BSTag) and child.name in ('ul', 'ol'):
                joined = ''.join(inline).strip()
                if joined:
                    buf.append(f'<p class="desc-para">{joined}</p>')
                inline = []
                _render_node(child, buf)
            else:
                _render_inline(child, inline)
        joined = ''.join(inline).strip()
        if joined:
            buf.append(f'<p class="desc-para">{joined}</p>')

    elif name in ('ul', 'ol'):
        items = []
        for child in node.children:
            if isinstance(child, BSTag) and child.name == 'li':
                li_parts = []
                for li_child in child.children:
                    _render_inline(li_child, li_parts)
                li_inner = ''.join(li_parts).strip()
                if li_inner:
                    items.append(f'<li>{li_inner}</li>')
        if items:
            items_html = ''.join(items)
            buf.append(f'<{name}>{items_html}</{name}>')

    elif name in ('strong', 'b'):
        t = node.get_text(strip=True)
        if t:
            buf.append(f'<p class="desc-para"><strong>{escape(t)}</strong></p>')

    elif name in ('em', 'i'):
        t = node.get_text(strip=True)
        if t:
            buf.append(f'<p class="desc-para"><em>{escape(t)}</em></p>')

    elif name in ('br', 'hr'):
        pass  # skip at block level

    else:
        # div, span, section, a, etc. — unwrap and recurse into children
        for child in node.children:
            _render_node(child, buf)


def format_description(text):
    """Render a project description as safe HTML.

    HTML content (from the new scraper) is parsed with BS4 and reconstructed
    as controlled, well-formed HTML.  Plain-text rows from before the HTML
    scraping update fall back to the paragraph-per-line formatter.
    """
    if not text:
        return Markup('')

    text = text.strip()

    if _HTML_RE.search(text):
        # Parse stored HTML and walk the tree to build controlled output.
        soup = BeautifulSoup(text, 'html.parser')
        container = soup.body if soup.body else soup
        buf = []
        for node in container.children:
            _render_node(node, buf)
        return Markup('\n'.join(buf))

    # Legacy plain-text fallback: one <p> per line, bold known section headers.
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    html = []
    for line in lines:
        line = re.sub(r'^>>\s*', '', line).strip()
        if not line:
            continue
        if line.lower().rstrip(':') in _TOP_HEADERS:
            html.append(f'<p class="desc-section"><strong>{escape(line.rstrip(":"))}</strong></p>')
        else:
            html.append(f'<p class="desc-para">{escape(line)}</p>')
    return Markup('\n'.join(html))


app.jinja_env.filters['format_description'] = format_description


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


# ------------------------------ Term Dropdown Helper ------------------------------ #

def generate_terms(years_back: int = 5) -> list:
    """Generate a list of academic quarter terms going back from the current quarter.

    Returns:
        list: Terms such as 'Spring 2026', 'Winter 2026', etc.
    """
    current_year = datetime.now().year
    current_month = datetime.now().month

    quarter_terms = ['Fall', 'Winter', 'Spring', 'Summer']

    if 9 <= current_month <= 12:
        start_index = 0
    elif 1 <= current_month <= 3:
        start_index = 1
    elif 4 <= current_month <= 6:
        start_index = 2
    else:
        start_index = 3

    terms = []
    year = current_year
    quarter = start_index

    for _ in range(years_back * 4):
        terms.append(f'{quarter_terms[quarter]} {year}')
        quarter -= 1
        if quarter < 0:
            quarter = 3
            year -= 1

    return terms


# ------------------------------ Public Routes ------------------------------ #

@app.route('/')
def home():
    """Render the project listing page with optional search, filter, and sort."""
    search_query = request.args.get('search', '').strip()
    sort_option = request.args.get('sort', 'title')
    try:
        page = max(1, int(request.args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    per_page = 10

    def parse_rating_filter(param):
        """Return int 1-5 if the query param is a valid rating, else None."""
        try:
            val = int(request.args.get(param, 0))
            return val if 1 <= val <= 5 else None
        except (ValueError, TypeError):
            return None

    filter_min_complexity = parse_rating_filter('min_complexity')
    filter_max_complexity = parse_rating_filter('max_complexity')
    filter_min_workload = parse_rating_filter('min_workload')
    filter_max_workload = parse_rating_filter('max_workload')
    filter_min_team_dynamics = parse_rating_filter('min_team_dynamics')
    filter_max_team_dynamics = parse_rating_filter('max_team_dynamics')
    filter_min_recommend = parse_rating_filter('min_recommend')
    filter_max_recommend = parse_rating_filter('max_recommend')
    filter_has_reviews = request.args.get('has_reviews') == '1'

    sort_options = {
        'title': 'p.title ASC',
        'most_reviews': 'review_count DESC, p.title ASC',
        'avg_score': 'avg_score DESC, p.title ASC',
        'highest_complexity': 'avg_complexity DESC, p.title ASC',
        'lowest_complexity': 'avg_complexity ASC, p.title ASC',
        'highest_workload': 'avg_workload DESC, p.title ASC',
        'lowest_workload': 'avg_workload ASC, p.title ASC',
        'highest_team_dynamics': 'avg_team_dynamics DESC, p.title ASC',
        'lowest_team_dynamics': 'avg_team_dynamics ASC, p.title ASC',
        'highest_recommendation': 'avg_recommend DESC, p.title ASC',
        'lowest_recommendation': 'avg_recommend ASC, p.title ASC',
    }
    order_by = sort_options.get(sort_option, sort_options['title'])

    where_clauses = []
    where_params = []
    having_clauses = []
    having_params = []

    if search_query:
        where_clauses.append('p.title LIKE %s')
        where_params.append(f'%{search_query}%')

    if filter_min_complexity:
        having_clauses.append('AVG(r.complexity) >= %s')
        having_params.append(filter_min_complexity)

    if filter_max_complexity:
        having_clauses.append('AVG(r.complexity) <= %s')
        having_params.append(filter_max_complexity)

    if filter_min_workload:
        having_clauses.append('AVG(r.workload) >= %s')
        having_params.append(filter_min_workload)

    if filter_max_workload:
        having_clauses.append('AVG(r.workload) <= %s')
        having_params.append(filter_max_workload)

    if filter_min_team_dynamics:
        having_clauses.append('AVG(r.team_dynamics) >= %s')
        having_params.append(filter_min_team_dynamics)

    if filter_max_team_dynamics:
        having_clauses.append('AVG(r.team_dynamics) <= %s')
        having_params.append(filter_max_team_dynamics)

    if filter_min_recommend:
        having_clauses.append('AVG(r.would_recommend) >= %s')
        having_params.append(filter_min_recommend)

    if filter_max_recommend:
        having_clauses.append('AVG(r.would_recommend) <= %s')
        having_params.append(filter_max_recommend)

    if filter_has_reviews:
        having_clauses.append('COUNT(r.review_id) > 0')

    where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''
    having_sql = ('HAVING ' + ' AND '.join(having_clauses)) if having_clauses else ''

    query = f"""
        SELECT
            p.project_id,
            p.title,
            p.description,
            p.image_url,
            COUNT(r.review_id)                                                  AS review_count,
            AVG(r.complexity)                                                   AS avg_complexity,
            AVG(r.workload)                                                     AS avg_workload,
            AVG(r.team_dynamics)                                                AS avg_team_dynamics,
            AVG(r.would_recommend)                                              AS avg_recommend,
            (AVG(r.complexity) + AVG(r.workload)
                + AVG(r.team_dynamics) + AVG(r.would_recommend)) / 4.0         AS avg_score,
            (SELECT r2.review_text FROM reviews r2
             WHERE r2.project_id = p.project_id
             ORDER BY r2.created_at DESC LIMIT 1)                              AS top_snippet,
            (SELECT s2.pseudonym FROM reviews r2
             JOIN students s2 ON r2.student_id = s2.student_id
             WHERE r2.project_id = p.project_id
             ORDER BY r2.created_at DESC LIMIT 1)                              AS top_pseudonym,
            (SELECT r2.term FROM reviews r2
             WHERE r2.project_id = p.project_id
             ORDER BY r2.created_at DESC LIMIT 1)                             AS top_term
        FROM projects p
        LEFT JOIN reviews r ON p.project_id = r.project_id
        {where_sql}
        GROUP BY p.project_id
        {having_sql}
        ORDER BY {order_by}
    """

    count_query = f"""
        SELECT COUNT(*) AS cnt FROM (
            SELECT p.project_id
            FROM projects p
            LEFT JOIN reviews r ON p.project_id = r.project_id
            {where_sql}
            GROUP BY p.project_id
            {having_sql}
        ) AS filtered
    """

    offset = (page - 1) * per_page
    paginated_query = query + f"\n    LIMIT {per_page} OFFSET {offset}"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) AS cnt FROM projects')
    total_count = cursor.fetchone()['cnt']
    cursor.execute(count_query, where_params + having_params)
    filtered_count = cursor.fetchone()['cnt']
    cursor.execute(paginated_query, where_params + having_params)
    projects = cursor.fetchall()
    conn.close()

    total_pages = max(1, (filtered_count + per_page - 1) // per_page)
    page = min(page, total_pages)

    return render_template(
        'index.html',
        projects=projects,
        search_query=search_query,
        sort_option=sort_option,
        filter_min_complexity=filter_min_complexity,
        filter_max_complexity=filter_max_complexity,
        filter_min_workload=filter_min_workload,
        filter_max_workload=filter_max_workload,
        filter_min_team_dynamics=filter_min_team_dynamics,
        filter_max_team_dynamics=filter_max_team_dynamics,
        filter_min_recommend=filter_min_recommend,
        filter_max_recommend=filter_max_recommend,
        filter_has_reviews=filter_has_reviews,
        filtered_count=filtered_count,
        total_count=total_count,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
    )


@app.route('/project/<int:project_id>')
def project_detail(project_id):
    """Render the project detail page with all reviews and comments."""
    review_term = request.args.get('review_term', '').strip() or None
    try:
        review_page = max(1, int(request.args.get('review_page', 1) or 1))
    except (ValueError, TypeError):
        review_page = 1
    reviews_per_page = 5
    review_order = 'helpful_count - not_helpful_count DESC, r.created_at DESC'

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            p.project_id,
            p.title,
            p.description,
            p.details,
            p.image_url,
            AVG(r.complexity) AS complexity,
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

    # distinct terms for filter dropdown
    cursor.execute(
        'SELECT DISTINCT term FROM reviews WHERE project_id = %s AND term IS NOT NULL ORDER BY term DESC',
        (project_id,)
    )
    review_terms = [row['term'] for row in cursor.fetchall()]

    # build review filter clause
    review_where_clauses = ['r.project_id = %s']
    review_params = [project_id]
    if review_term:
        review_where_clauses.append('r.term = %s')
        review_params.append(review_term)
    review_where_sql = 'WHERE ' + ' AND '.join(review_where_clauses)

    # total count for pagination
    cursor.execute(f'SELECT COUNT(*) AS cnt FROM reviews r {review_where_sql}', review_params)
    review_count = cursor.fetchone()['cnt']
    review_total_pages = max(1, (review_count + reviews_per_page - 1) // reviews_per_page)
    review_page = min(review_page, review_total_pages)
    review_offset = (review_page - 1) * reviews_per_page

    cursor.execute("""
        SELECT
            r.review_id,
            r.student_id,
            r.review_text,
            r.ai_use,
            r.term,
            r.complexity,
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
        {review_where_sql}
        ORDER BY {review_order}
        LIMIT {per_page} OFFSET {offset}
    """.format(
        review_where_sql=review_where_sql,
        review_order=review_order,
        per_page=reviews_per_page,
        offset=review_offset,
    ), review_params)

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

    # fetch comments only for visible reviews
    comments = []
    comment_votes = {}
    if reviews:
        review_ids = [r['review_id'] for r in reviews]
        placeholders = ', '.join(['%s'] * len(review_ids))
        cursor.execute(f"""
            SELECT
                c.comment_id,
                c.review_id,
                c.comment_text,
                c.created_at,
                s.pseudonym,
                (SELECT COUNT(*) FROM comment_helpfulness ch
                 WHERE ch.comment_id = c.comment_id AND ch.value = 1)  AS helpful_count,
                (SELECT COUNT(*) FROM comment_helpfulness ch
                 WHERE ch.comment_id = c.comment_id AND ch.value = -1) AS not_helpful_count
            FROM comments c
            JOIN students s ON c.student_id = s.student_id
            WHERE c.review_id IN ({placeholders})
            ORDER BY helpful_count - not_helpful_count DESC, c.created_at ASC
        """, review_ids)
        comments = cursor.fetchall()

        if 'student_id' in session and comments:
            comment_ids = [c['comment_id'] for c in comments]
            c_placeholders = ', '.join(['%s'] * len(comment_ids))
            cursor.execute(
                f'SELECT comment_id, value FROM comment_helpfulness'
                f' WHERE student_id = %s AND comment_id IN ({c_placeholders})',
                [session['student_id']] + comment_ids
            )
            comment_votes = {row['comment_id']: row['value'] for row in cursor.fetchall()}

    conn.close()

    return render_template(
        'project_detail.html',
        project=project,
        reviews=reviews,
        comments=comments,
        user_votes=user_votes,
        comment_votes=comment_votes,
        review_term=review_term,
        review_terms=review_terms,
        review_count=review_count,
        review_page=review_page,
        review_total_pages=review_total_pages,
        reviews_per_page=reviews_per_page,
    )


@app.route('/project/<int:project_id>/submit-review', methods=['GET', 'POST'])
@login_required
def submit_review(project_id):
    """Display and process the review submission page."""
    if request.method == 'POST':
        term = request.form.get('term', '').strip()
        ai_use = request.form.get('ai_use', '').strip() or None

        try:
            complexity = int(request.form.get('complexity'))
            workload = int(request.form.get('workload'))
            team_dynamics = int(request.form.get('team_dynamics'))
            would_recommend = int(request.form.get('would_recommend'))
            ratings = [complexity, workload, team_dynamics, would_recommend]
            if not all(1 <= r <= 5 for r in ratings):
                return 'Ratings must be between 1 and 5', 400
        except (TypeError, ValueError):
            return 'Invalid rating value', 400

        review_text = request.form.get('review_text', '').strip()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reviews
                    (project_id, student_id, term, complexity, workload,
                     team_dynamics, would_recommend, review_text, ai_use)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                project_id, session['student_id'], term,
                complexity, workload, team_dynamics, would_recommend,
                review_text, ai_use,
            ))
            conn.commit()
        finally:
            conn.close()

        flash('Your review has been submitted.', 'success')
        return redirect(url_for('project_detail', project_id=project_id))

    terms = generate_terms()
    return render_template('submit_review.html', project_id=project_id, terms=terms)


@app.route('/review/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    """Display and process the review edit page."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reviews WHERE review_id = %s', (review_id,))
    review = cursor.fetchone()

    if review is None:
        conn.close()
        return 'Review not found', 404

    if review['student_id'] != session['student_id']:
        conn.close()
        return 'Unauthorized', 403

    if request.method == 'POST':
        term = request.form.get('term', '').strip()
        ai_use = request.form.get('ai_use', '').strip() or None

        try:
            complexity = int(request.form.get('complexity'))
            workload = int(request.form.get('workload'))
            team_dynamics = int(request.form.get('team_dynamics'))
            would_recommend = int(request.form.get('would_recommend'))
            ratings = [complexity, workload, team_dynamics, would_recommend]
            if not all(1 <= r <= 5 for r in ratings):
                conn.close()
                return 'Ratings must be between 1 and 5', 400
        except (TypeError, ValueError):
            conn.close()
            return 'Invalid rating value', 400

        review_text = request.form.get('review_text', '').strip()
        project_id = review['project_id']

        try:
            cursor.execute("""
                UPDATE reviews
                SET term = %s, complexity = %s, workload = %s,
                    team_dynamics = %s, would_recommend = %s,
                    review_text = %s, ai_use = %s
                WHERE review_id = %s
            """, (
                term, complexity, workload, team_dynamics, would_recommend,
                review_text, ai_use, review_id,
            ))
            conn.commit()
        finally:
            conn.close()

        flash('Your review has been updated.', 'success')
        return redirect(url_for('project_detail', project_id=project_id))

    conn.close()
    terms = generate_terms()
    return render_template('edit_review.html', review=review, terms=terms)


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

    flash('Comment posted.', 'success')
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


@app.route('/comment/<int:comment_id>/vote', methods=['POST'])
@login_required
def vote_comment(comment_id):
    """Toggle a helpful (1) or not-helpful (-1) vote on a comment.

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
            'SELECT value FROM comment_helpfulness WHERE comment_id = %s AND student_id = %s',
            (comment_id, student_id)
        )
        existing = cursor.fetchone()

        if existing:
            if existing['value'] == value:
                cursor.execute(
                    'DELETE FROM comment_helpfulness WHERE comment_id = %s AND student_id = %s',
                    (comment_id, student_id)
                )
            else:
                cursor.execute(
                    'UPDATE comment_helpfulness SET value = %s WHERE comment_id = %s AND student_id = %s',
                    (value, comment_id, student_id)
                )
        else:
            cursor.execute(
                'INSERT INTO comment_helpfulness (comment_id, student_id, value) VALUES (%s, %s, %s)',
                (comment_id, student_id, value)
            )

        conn.commit()
    finally:
        conn.close()

    return redirect(url_for('project_detail', project_id=project_id))


# ------------------------------ Error Handlers ------------------------------ #

@app.errorhandler(404)
def not_found(e):
    """Render the custom 404 page."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """Render the custom 500 page."""
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
