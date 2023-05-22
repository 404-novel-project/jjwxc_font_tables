from flask import (
    Blueprint, render_template, make_response, abort, request
)

from .font_parser import validator
from .font_parser.slow import match_jjwxc_font_tool

bp = Blueprint('tools', __name__, url_prefix='/tools')


@bp.route('/slow-match/jjwxc', methods=('GET', 'POST'))
async def slow_match_jjwxc():
    if request.method == 'POST':
        jjwxc_font_name = request.form['jjwxc_font_name']
        if not validator(jjwxc_font_name):
            return abort(403)

        result, status = await match_jjwxc_font_tool(jjwxc_font_name,
                                                     {"std_font": request.form['std_font'],
                                                      "guest_range": request.form['guest_range']})
        if status == 200:
            return make_response(result)
        else:
            return abort(status)

    return render_template('tools/slow_match_jjwxc.html')
