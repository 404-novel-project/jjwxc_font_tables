import pytest


def test_get_list(client):
    response = client.get('/html/')
    assert response.status_code == 200


@pytest.mark.parametrize('font_name', (
        'jjwxcfont_2o8eo', 'jjwxcfont_2odzt',
))
def test_get_font_200(client, font_name):
    response = client.get('/html/')
    assert response.status_code == 200


@pytest.mark.parametrize('font_name', (
        'jjwxcfont_3o8eo', 'jjwxcfont_3odzt',
))
def test_get_font_404(client, font_name):
    response = client.get('/html/{}'.format(font_name))
    assert response.status_code == 404
