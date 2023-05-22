name = 'jjwxc_font_tables'
__version__ = '0.1.0'

import json
import os
import shutil

from flask import Flask, Response


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI='sqlite:///{}'.format(os.path.join(app.instance_path, 'jjwxc.sqlite')),
        COORD_TABLE_PATH=os.path.join(app.instance_path, 'coorTable.json'),
        SOURCE_HAN_SANS_SC_NORMAL_PATH=os.path.join(app.root_path, 'font_parser/assets/SourceHanSansSC-Normal.otf'),
        SOURCE_HAN_SANS_SC_REGULAR_PATH=os.path.join(app.root_path, 'font_parser/assets/SourceHanSansSC-Regular.otf'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    with app.app_context():
        init(app)

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

    return app


def init(app: Flask):
    # 创建 instance 目录
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    # 初始化数据库
    from . import db
    db.init_app(app)

    if not os.path.exists(os.path.join(app.instance_path, 'jjwxc.sqlite')):
        db.init_db()

    # 复制 coorTable.json
    if not os.path.exists(app.config.get('COORD_TABLE_PATH')):
        shutil.copy(
            os.path.join(app.root_path, 'font_parser/assets/coorTable.json'),
            app.config.get('COORD_TABLE_PATH')
        )
    else:
        try:
            with open(app.config.get('COORD_TABLE_PATH'), 'r') as f:
                local_coorTable = json.load(f)
            with open(os.path.join(app.root_path, 'font_parser/assets/coorTable.json'), 'r') as f:
                remote_coorTable = json.load(f)
        except json.decoder.JSONDecodeError:
            shutil.copy(
                os.path.join(app.root_path, 'font_parser/assets/coorTable.json'),
                app.config.get('COORD_TABLE_PATH')
            )
