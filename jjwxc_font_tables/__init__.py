name = 'jjwxc_font_tables'
__version__ = '0.1.0'

import os

from flask import Flask, current_app
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI='sqlite:///{}'.format(
            os.path.join(app.instance_path, 'jjwxc.sqlite')
        ),
        PROXY=True
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    with app.app_context():
        from . import db
        db.init_app(app)

        from . import healthcheck
        app.register_blueprint(healthcheck.bp)

        from . import index
        app.register_blueprint(index.bp)

        from . import api
        app.register_blueprint(api.bp)

        from . import html
        app.register_blueprint(html.bp)

        if current_app.config.get('PROXY'):
            app.wsgi_app = ProxyFix(
                app.wsgi_app, x_for=1, x_proto=1
            )

    return app
