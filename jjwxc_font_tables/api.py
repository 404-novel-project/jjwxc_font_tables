from flask import Blueprint, Response, jsonify, abort

from .font_parser import match
from .lib import add_etag

bp = Blueprint('api', __name__, url_prefix='/api')


def add_cors_and_cache_headers(response: Response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
    response.headers.add('Access-Control-Expose-Headers',
                         'Etag, Content-Length, Accept-Ranges, Content-Range')
    response.headers.add('Access-Control-Max-Age', '86400')
    response.headers.add('Cache-Control', 'max-age=2678400')
    return response


@bp.after_request
def api_after_request(response: Response):
    add_cors_and_cache_headers(response)
    return response


@bp.route('/<font_name>')
async def get_font(font_name: str):
    font, status_code = await match(font_name)
    if status_code == 200:
        _font = font.to_dict()
        _font.pop('bytes', None)
        response = jsonify(_font)
        add_etag(response)
        return response
    else:
        return abort(status_code)


@bp.route('/<font_name>/table')
async def get_table(font_name: str):
    font, status_code = await match(font_name)
    if status_code == 200:
        response = jsonify(font.table)
        add_etag(response)
        return response
    else:
        return abort(status_code)


@bp.route('/<font_name>/bytes')
async def get_bytes(font_name: str):
    font, status_code = await match(font_name)
    if status_code == 200:
        response = Response(font.bytes, mimetype='application/font-woff2')
        response.headers.add('Content-Disposition',
                             'attachment; filename="{}.woff"'.format(font.name))
        add_etag(response)
        return response
    else:
        return abort(status_code)
