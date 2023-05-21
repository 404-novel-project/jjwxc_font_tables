import hashlib

import pytest


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_2o8eo', 'jjwxcfont_2odzt',
))
def test_get_font_200(app, client, font_name: str):
    response = client.get('/api/{}'.format(font_name))
    assert response.status_code == 200
    assert response.headers.get('Content-Type') == 'application/json'

    m = hashlib.sha1()
    m.update(response.data)
    assert response.headers.get('ETag') == '"{}"'.format(m.hexdigest())


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_3o8eo',
))
def test_get_font_404(app, client, font_name: str):
    response = client.get('/api/{}'.format(font_name))
    assert response.status_code == 404


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_3o8ddeo', 'jjwxcfont_3o8ddedsafo',
        'jjwxcfont_2o\\8eo', 'jjwxlcfont_2o8eo'
))
def test_get_font_403(app, client, font_name: str):
    response = client.get('/api/{}'.format(font_name))
    assert response.status_code == 403


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_2o8eo', 'jjwxcfont_2odzt',
))
def test_get_table_200(app, client, font_name: str):
    response = client.get('/api/{}/table'.format(font_name))
    assert response.status_code == 200
    assert response.headers.get('Content-Type') == 'application/json'

    m = hashlib.sha1()
    m.update(response.data)
    assert response.headers.get('ETag') == '"{}"'.format(m.hexdigest())


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_3o8eo', 'jjwxcfont_3odzt',
        'jjwxcfont_2o8eo/89833', 'jjwxcfont_2o8e/o/',
))
def test_get_table_404(app, client, font_name: str):
    response = client.get('/api/{}/table'.format(font_name))
    assert response.status_code == 404


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfon_3o8eo', 'jjwxcfont__3odzt', '2o8eo_kf',
        "jjwxcfont_2o'8eo", 'jjwxcfont_2o"\dzt',
))
def test_get_table_403(app, client, font_name: str):
    response = client.get('/api/{}/table'.format(font_name))
    assert response.status_code == 403


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_2o8eo', 'jjwxcfont_2odzt',
))
def test_get_bytes_200(app, client, font_name: str):
    response = client.get('/api/{}/bytes'.format(font_name))
    assert response.status_code == 200
    assert response.headers.get('Content-Type') == 'application/font-woff2'

    m = hashlib.sha1()
    m.update(response.data)
    assert response.headers.get('ETag') == '"{}"'.format(m.hexdigest())

    assert response.headers.get('Content-Disposition') == 'attachment; filename="{}.woff"'.format(font_name)


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_3o8eo', 'jjwxcfont_3odzt',
))
def test_get_bytes_404(app, client, font_name: str):
    response = client.get('/api/{}/bytes'.format(font_name))
    assert response.status_code == 404


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_3o8eo_', 'jjwxcfon__3odzt',
))
def test_get_bytes_403(app, client, font_name: str):
    response = client.get('/api/{}/bytes'.format(font_name))
    assert response.status_code == 403


def run_cors_test(func, path: str):
    response = func(path)
    assert response.status_code == 200
    assert response.headers.get('access-control-allow-origin') == '*'
    assert response.headers.get(('access-control-allow-methods')) == 'GET, HEAD, OPTIONS'


@pytest.mark.parametrize(('path'), (
        '/api/jjwxcfont_2o8eo', '/api/jjwxcfont_2odzt',
        '/api/jjwxcfont_2o8eo/table', '/api/jjwxcfont_2odzt/table',
        '/api/jjwxcfont_2o8eo/bytes', '/api/jjwxcfont_2odzt/bytes',
))
def test_get_CORS(app, client, path: str):
    run_cors_test(client.get, path)
    run_cors_test(client.options, path)


@pytest.mark.parametrize(('path'), (
        '/api/jjwxcfont_2o8eo', '/api/jjwxcfont_2odzt',
        '/api/jjwxcfont_2o8eo/table', '/api/jjwxcfont_2odzt/table',
        '/api/jjwxcfont_2o8eo/bytes', '/api/jjwxcfont_2odzt/bytes',
))
def test_options_CORS(app, client, path: str):
    run_cors_test(client.options, path)
