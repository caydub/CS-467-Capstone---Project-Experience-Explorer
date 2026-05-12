import pytest
from unittest.mock import MagicMock, patch
from main import app as flask_app


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_db():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    with patch('main.get_db_connection', return_value=mock_conn):
        yield mock_cursor
