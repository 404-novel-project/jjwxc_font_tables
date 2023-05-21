from flask import Blueprint, make_response

bp = Blueprint('healthcheck', __name__)


@bp.route('/healthcheck')
def healthcheck():
    return make_response("OK", 200)
