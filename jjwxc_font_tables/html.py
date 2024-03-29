import sqlalchemy as sa
from flask import Blueprint, render_template, make_response, abort

from .cache import cache
from .db import db, Font
from .font_parser import match_jjwxc_font
from .lib import add_etag, get_charater_hex

bp = Blueprint('html', __name__, url_prefix='/html')


@bp.route('/')
def get_list():
    font_name_list = db.session.execute(
        sa.select(Font.name).order_by(Font.name.desc())
    ).fetchall()
    _font_name_list = sorted(list(map(
        lambda x: x[0], font_name_list
    )))

    return render_template('list.html', font_name_list=_font_name_list)


@cache.cached
@bp.route('/<font_name>')
async def get_font(font_name: str):
    font, status_code = await match_jjwxc_font(font_name)

    if status_code == 200:
        output = render_template('font.html', font=font.to_dict(), get_charater_hex=get_charater_hex)
        response = make_response(output)

        response.headers.add('Cache-Control', 'max-age=2678400')
        add_etag(response)

        return response
    else:
        return abort(status_code)
