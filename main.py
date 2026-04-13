import os
import pymysql
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

db_config = {
    'host': '127.0.0.1',
    'user': 'flask_user',
    'password': os.environ.get('DB_PASSWORD'),
    'database': 'project_explorer_db',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    return pymysql.connect(**db_config)

@app.route('/')
def index():
    return 'Project Experience Explorer is running!'

@app.route('/test-db')
def test_db():
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