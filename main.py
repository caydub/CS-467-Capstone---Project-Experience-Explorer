import os
import pymysql
from flask import Flask, render_template, request
from dotenv import load_dotenv

# Load variables from .env file into the environment (local development only)
load_dotenv()

app = Flask(__name__)


def get_secret(secret_id):
    """Fetch a secret value from GCP Secret Manager.

    Used when running on App Engine to avoid storing passwords in code or config files.
    """
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/project-experience-explorer/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


if os.environ.get('GAE_ENV', '').startswith('standard'):
    db_password = get_secret('db_flask_user_password')
else:
    db_password = os.environ.get('DB_PASSWORD')


db_config = {
    'user': 'flask_user',
    'password': db_password,
    'database': 'project_explorer_db',
    'cursorclass': pymysql.cursors.DictCursor
}

if os.environ.get('GAE_ENV', '').startswith('standard'):
    db_config['unix_socket'] = (
        '/cloudsql/project-experience-explorer:us-central1:'
        'project-experience-explorer-db'
    )
else:
    db_config['host'] = '127.0.0.1'


def get_db_connection():
    """Open and return a new database connection."""
    return pymysql.connect(**db_config)


@app.route('/')
def home():
    """Render the project listing page with optional search filtering."""
    search_query = request.args.get('search', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        cursor.execute("""
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
            WHERE p.title LIKE %s
            GROUP BY p.project_id
            ORDER BY p.title
        """, (f'%{search_query}%',))
    else:
        cursor.execute("""
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
            GROUP BY p.project_id
            ORDER BY p.title
        """)

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
def submit_review(project_id):
    """Display the review submission page."""
    return render_template('submit_review.html', project_id=project_id)


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