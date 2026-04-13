import os
import pymysql
from flask import Flask, render_template
from dotenv import load_dotenv

# load variables from .env file into the environment (local development only)
load_dotenv()

app = Flask(__name__)


def get_secret(secret_id):
    """Fetch a secret value from GCP Secret Manager.

    Used when running on App Engine to avoid storing passwords in code or config files.
    """
    from google.cloud import secretmanager
    client = secretmanager.SecretManagerServiceClient()
    # build the full path to the secret — always fetch the latest version
    name = f"projects/project-experience-explorer/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    # decode the secret from bytes to a plain string
    return response.payload.data.decode("UTF-8")


# GAE_ENV is automatically set by App Engine when running in the cloud
# if it starts with 'standard' we're on App Engine, otherwise we're running locally
if os.environ.get('GAE_ENV', '').startswith('standard'):
    # on App Engine — get password securely from Secret Manager
    db_password = get_secret('db_flask_user_password')
else:
    # running locally — get password from .env file
    db_password = os.environ.get('DB_PASSWORD')

# database connection configuration
# user/password/database are the same in both environments
db_config = {
    'user': 'flask_user',
    'password': db_password,
    'database': 'project_explorer_db',
    # DictCursor means query results come back as dictionaries
    # e.g. {'id': 1, 'name': 'foo'} instead of (1, 'foo')
    'cursorclass': pymysql.cursors.DictCursor
}

# App Engine connects to Cloud SQL via a Unix socket (a file-based connection)
# locally we connect via TCP through the Cloud SQL Auth Proxy on port 3306
if os.environ.get('GAE_ENV', '').startswith('standard'):
    # unix socket path follows this exact format — don't change it
    db_config['unix_socket'] = '/cloudsql/project-experience-explorer:us-central1:project-experience-explorer-db'
else:
    # proxy listens on localhost port 3306 by default
    db_config['host'] = '127.0.0.1'


def get_db_connection():
    """Open and return a new database connection.

    Call this at the start of any route that needs to query the database.
    Always close the connection when done.
    """
    return pymysql.connect(**db_config)


@app.route('/')
def index():
    return 'Project Experience Explorer is running!'


@app.route('/test-db')
def test_db():
    """Temporary route to verify the database connection is working.

    Remove this before final deployment.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # simple query that just returns 1 — used to confirm connection works
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        conn.close()
        return f'Database connection successful! Result: {result}'
    except Exception as e:
        return f'Database connection failed: {str(e)}'


if __name__ == '__main__':
    # this block only runs when you execute main.py directly (local dev)
    # on App Engine, gunicorn starts the app instead and this is ignored
    app.run(host='127.0.0.1', port=8080, debug=True)