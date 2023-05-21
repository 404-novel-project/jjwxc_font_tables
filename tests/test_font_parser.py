import pytest

from jjwxc_font_tables.font_parser import download
from jjwxc_font_tables.font_parser import quick

pytest_plugins = ('pytest_asyncio',)
# # # All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio


async def get_font(font_name: str):
    r = await download.get_font(font_name)
    print(r.get('name'), r.get('hashsum'), r.get('status'))
    return r


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_2o8eo', 'jjwxcfont_2odzt',
))
async def test_get_font_ok(font_name: str):
    r = await get_font(font_name)
    assert r['status'] == 'OK'


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_3o8eo',
))
async def test_get_font_404(font_name: str):
    r = await get_font(font_name)
    assert r['status'] == '404'


@pytest.mark.parametrize(('font_name'), (
        'jjwxcfont_2o8eo', 'jjwxcfont_2odzt',
))
async def test_quick_match(font_name: str):
    font = await download.get_font(font_name)
    return quick.match_font(font.get('ttf'))
