def test_home_returns_200(client, mock_db):
    mock_db.fetchone.side_effect = [{'cnt': 0}, {'cnt': 0}]
    mock_db.fetchall.return_value = []
    response = client.get('/')
    assert response.status_code == 200


def test_home_lists_projects(client, mock_db):
    mock_db.fetchone.side_effect = [{'cnt': 1}, {'cnt': 1}]
    mock_db.fetchall.return_value = [
        {
            'project_id': 1,
            'title': 'Test Project',
            'description': 'A test project',
            'image_url': None,
            'review_count': 0,
            'avg_complexity': None,
            'avg_workload': None,
            'avg_team_dynamics': None,
            'avg_recommend': None,
            'avg_score': None,
            'top_snippet': None,
            'top_pseudonym': None,
            'top_term': None,
        }
    ]
    response = client.get('/')
    assert b'Test Project' in response.data


def test_home_search_returns_200(client, mock_db):
    mock_db.fetchone.side_effect = [{'cnt': 0}, {'cnt': 0}]
    mock_db.fetchall.return_value = []
    response = client.get('/?search=test')
    assert response.status_code == 200


def test_project_detail_returns_200(client, mock_db):
    mock_db.fetchone.side_effect = [
        {
            'project_id': 1,
            'title': 'Test Project',
            'description': 'A test project',
            'details': None,
            'image_url': None,
            'url': None,
            'avg_complexity': None,
            'avg_workload': None,
            'avg_team_dynamics': None,
            'avg_recommend': None,
        },
        {'cnt': 0},  # review_count
    ]
    mock_db.fetchall.return_value = []  # review_terms, reviews, comments
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
    mock_db.fetchone.return_value = None  # no existing review for this project
    with client.session_transaction() as sess:
        sess['student_id'] = 1
        sess['pseudonym'] = 'BoldRaven42'
    response = client.get('/project/1/submit-review')
    assert response.status_code == 200
