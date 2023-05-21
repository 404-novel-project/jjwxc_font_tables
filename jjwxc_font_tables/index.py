import os

from flask import Blueprint, redirect, url_for, Response, send_from_directory, current_app

bp = Blueprint('index', __name__)


@bp.route('/')
def index():
    return redirect(url_for('html.get_list'))


@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@bp.route('/robots.txt')
def robots():
    return Response('User-agent: *\nDisallow: /', mimetype="text/plain")


@bp.route('/<font_name>.json')
def old_font_table(font_name: str):
    return redirect(url_for('api.get_table', font_name=font_name))
