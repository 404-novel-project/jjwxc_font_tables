name = 'jjwxc_font_tables'
__version__ = '0.1.0'

import os

from flask import Flask, current_app, Response
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI='sqlite:///{}'.format(
            os.path.join(app.instance_path, 'jjwxc.sqlite')
        ),
        PROXYFIX=False
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    with app.app_context():
        if not os.path.exists(app.instance_path):
            os.makedirs(app.instance_path)

        from . import db
        db.init_app(app)

        if not os.path.exists(os.path.join(app.instance_path, 'jjwxc.sqlite')):
            db.init_db()

        from . import healthcheck
        app.register_blueprint(healthcheck.bp)

        from . import index
        app.register_blueprint(index.bp)

        from . import api
        app.register_blueprint(api.bp)

        from . import html
        app.register_blueprint(html.bp)

        @app.after_request
        def after(response: Response):
            response.headers.add('Referrer-Policy', 'same-origin')
            return response

        if current_app.config.get('PROXYFIX'):
            app.wsgi_app = ProxyFix(
                app.wsgi_app, x_for=1, x_proto=1
            )

    return app
