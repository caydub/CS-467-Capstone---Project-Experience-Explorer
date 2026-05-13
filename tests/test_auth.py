import hashlib
from unittest.mock import MagicMock, patch
from main import get_or_create_student, generate_unique_pseudonym


def test_get_or_create_student_returns_existing():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'student_id': 5, 'pseudonym': 'BoldRaven42'}

    with patch('main.get_db_connection', return_value=mock_conn):
        result = get_or_create_student('testuser')

    assert result['student_id'] == 5
    assert result['pseudonym'] == 'BoldRaven42'
    mock_conn.commit.assert_not_called()


def test_get_or_create_student_creates_new():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.lastrowid = 99

    with patch('main.get_db_connection', return_value=mock_conn):
        with patch('main.generate_unique_pseudonym', return_value='CalmFox7'):
            result = get_or_create_student('newuser')

    assert result['student_id'] == 99
    assert result['pseudonym'] == 'CalmFox7'
    mock_conn.commit.assert_called_once()


def test_get_or_create_student_hashes_onid():
    """Raw ONID should never be stored -- verify the SELECT uses the hash."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'student_id': 1, 'pseudonym': 'SwiftElm3'}

    with patch('main.get_db_connection', return_value=mock_conn):
        get_or_create_student('TestUser')  # mixed case

    expected_hash = hashlib.sha256('testuser'.encode()).hexdigest()  # lowercased
    args = mock_cursor.execute.call_args[0]
    assert expected_hash in args[1]
    assert 'TestUser' not in str(args[1])
    assert 'testuser' not in str(args[1])


def test_generate_unique_pseudonym_returns_string():
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    result = generate_unique_pseudonym(mock_cursor)
    assert isinstance(result, str)
    assert len(result) > 0
    assert any(char.isdigit() for char in result)


def test_generate_unique_pseudonym_retries_on_collision():
    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = [
        {'pseudonym': 'BoldRaven1'},  # first candidate already exists
        None,                          # second candidate is available
    ]
    result = generate_unique_pseudonym(mock_cursor)
    assert result is not None
    assert mock_cursor.execute.call_count == 2
