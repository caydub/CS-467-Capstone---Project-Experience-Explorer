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


projects = {
    1: {
        'id': 1,
        'title': 'AR Arcade Classics',
        'workload': 'High',
        'difficulty': '8/10',
        'difficulty_score': 8,
        'recommend': 'Yes',
        'review_count': 1,
        'top_snippet': (
            'Fun project with a lot of creative freedom, but it can get difficult '
            'as there are a lot of moving parts.'
        ),
        'description': (
            'You will recreate one or more classic arcade games in Augmented '
            'Reality and/or Virtual Reality. You choose the game(s). You choose '
            'AR, VR, or both!'
        )
    },

    2: {
        'id': 2,
        'title': 'Job Tracker',
        'workload': 'Medium',
        'difficulty': '5/10',
        'difficulty_score': 5,
        'recommend': 'Yes',
        'review_count': 1,
        'top_snippet': (
            'Fairly straightforward project that can be as detailed as the '
            'student wants, depending on number of features built.'
        ),
        'description': (
            'This web app allows students to track their internship/job hunting '
            'efforts. The target users would be CS students who are attempting '
            'to land internships and full time positions upon graduation.'
        )
    },

    3: {
        'id': 3,
        'title': 'Mobile Treasure Hunt - Cross-Platform',
        'workload': 'Very High',
        'difficulty': '8/10',
        'difficulty_score': 8,
        'recommend': 'Yes',
        'review_count': 1,
        'top_snippet': 'Fun but slightly difficult project.',
        'description': (
            'Mobile treasure hunt game that gives clues and uses GPS to determine '
            'if the user has solved the clue. Each clue can lead to the next and '
            'so on until the treasure is found.'
        )
    }
}

reviews = {
    1: [
        {
            'reviewer': 'user1',
            'term': 'Spring 2025',
            'text': (
                'Fun project with a lot of creative freedom, but it can get '
                'difficult as there are a lot of moving parts.'
            )
        },
    ],
    2: [
        {
            'reviewer': 'user2',
            'term': 'Fall 2025',
            'text': (
                'Fairly straightforward project that can be as detailed as the '
                'student wants, depending on number of features built.'
            )
        }
    ],
    3: [
        {
            'reviewer': 'user3',
            'term': 'Winter 2025',
            'text': 'Fun but slightly difficult project.'
        }
    ]
}


@app.route('/')
def home():
    search_query = request.args.get('search', '').strip()

    if search_query:
        filtered_projects = [
            project for project in projects.values()
            if search_query.lower() in project['title'].lower()
        ]
    else:
        filtered_projects = list(projects.values())

    return render_template(
        'index.html',
        projects=filtered_projects,
        search_query=search_query
    )


@app.route('/project/<int:id>')
def project_detail(id):
    project = projects.get(id)

    if project is None:
        return "Project not found", 404

    project_reviews = reviews.get(id, [])
    return render_template(
        'project_detail.html',
        project=project,
        reviews=project_reviews
    )


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