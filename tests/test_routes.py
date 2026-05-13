def test_home_returns_200(client, mock_db):
    mock_db.fetchall.return_value = []
    response = client.get('/')
    assert response.status_code == 200


def test_home_lists_projects(client, mock_db):
    mock_db.fetchall.return_value = [
        {
            'project_id': 1,
            'title': 'Test Project',
            'description': 'A test project',
            'review_count': 0,
            'difficulty': None,
            'workload': None,
            'would_recommend': None,
            'top_snippet': None,
        }
    ]
    response = client.get('/')
    assert b'Test Project' in response.data


def test_home_search_returns_200(client, mock_db):
    mock_db.fetchall.return_value = []
    response = client.get('/?search=test')
    assert response.status_code == 200


def test_project_detail_returns_200(client, mock_db):
    mock_db.fetchone.return_value = {
        'project_id': 1,
        'title': 'Test Project',
        'description': 'A test project',
        'difficulty': None,
        'workload': None,
        'team_dynamics': None,
        'would_recommend': None,
    }
    mock_db.fetchall.return_value = []
    response = client.get('/project/1')
    assert response.status_code == 200


def test_project_detail_404(client, mock_db):
    mock_db.fetchone.return_value = None
    response = client.get('/project/999')
    assert response.status_code == 404


def test_submit_review_redirects_when_unauthenticated(client, mock_db):
    response = client.get('/project/1/submit-review')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_submit_review_returns_200_when_authenticated(client, mock_db):
    with client.session_transaction() as sess:
        sess['student_id'] = 1
        sess['pseudonym'] = 'BoldRaven42'
    response = client.get('/project/1/submit-review')
    assert response.status_code == 200
