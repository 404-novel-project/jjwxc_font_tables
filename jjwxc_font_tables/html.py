import sqlalchemy as sa
from flask import Blueprint, render_template, make_response, abort

from .db import db, Font
from .font_parser import match
from .lib import add_etag

bp = Blueprint('html', __name__, url_prefix='/html')


@bp.route('/')
def get_list():
    font_name_list = db.session.execute(
        sa.select(Font.name)
    ).fetchall()
    _font_name_list = sorted(list(map(
        lambda x: x[0], font_name_list
    )))

    return render_template('list.html', font_name_list=_font_name_list)


@bp.route('/<font_name>')
async def get_font(font_name: str):
    def get_charater_hex(chac: str):
        return str(hex(ord(chac))).replace('0x', 'U+')

    font, status_code = await match(font_name)

    if status_code == 200:
        output = render_template('font.html', font=font.toDict(), get_charater_hex=get_charater_hex)
        response = make_response(output)

        response.headers.add('Cache-Control', 'max-age=2678400')
        add_etag(response)

        return response
    else:
        return abort(status_code)
