import pytest


def test_get_index(client):
    response = client.get('/')
    assert response.status_code == 302


@pytest.mark.parametrize('font_name', (
        'jjwxcfont_2o8eo',
))
def test_get_old_font_table(client, font_name):
    response = client.get('/{}.json'.format(font_name))
    assert response.status_code == 302
    assert response.headers.get('Location') == '/api/{}/table'.format(font_name)
