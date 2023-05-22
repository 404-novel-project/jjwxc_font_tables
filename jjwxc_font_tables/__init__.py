import copy
import json
import os
import shutil

from flask import Flask, Response

name = 'jjwxc_font_tables'
__version__ = '0.1.0'


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


def is_coor_match(x, y) -> bool:
    """比较 coor"""

    # 如果字符 coor 长度相同
    if len(x) == len(y):
        match = True
        # 逐一比较各点
        for ii in range(len(x)):
            rx, ry = x[ii]
            lx, ly = y[ii]
            if rx != lx or ry != ly:
                match = False
                break
        return match
    else:
        return False


def merge_coor_table(source, target):
    source_copy = copy.copy(source)
    for j in source:
        for k in target:
            if j[0] == k[0] and is_coor_match(j[1], k[1]):
                source_copy.remove(j)
    return sorted([*target, *source_copy], key=lambda x: x[0])


def deduplicate_coor_table(source: list):
    rm_list = []
    source_length = len(source)
    for j in range(source_length):
        for k in range(source_length):
            if j > k and \
                    source[j][0] == source[k][0] and is_coor_match(source[j][1], source[k][1]):
                if k not in rm_list:
                    rm_list.append(k)

    target = []
    for index, value in enumerate(source):
        if index not in rm_list:
            target.append(value)

    return target


def merge_and_deduplicate_coor_table(app: Flask):
    """将远程 coorTable 合并至本地"""
    with open(app.config.get('COORD_TABLE_PATH'), 'r') as f:
        _local_coorTable = json.load(f)
        local_coor_table = sorted(_local_coorTable, key=lambda x: x[0])
    with open(os.path.join(app.root_path, 'font_parser/assets/coorTable.json'), 'r') as f:
        _remote_coorTable = json.load(f)
        remote_coor_able: list[
            tuple[
                str,
                list[tuple[int, int]]
            ]
        ] = sorted(_remote_coorTable, key=lambda x: x[0])

    new_local_coor_table = merge_coor_table(remote_coor_able, local_coor_table)
    new_local_coor_table = deduplicate_coor_table(new_local_coor_table)

    if len(new_local_coor_table) != len(local_coor_table):
        if len(new_local_coor_table) != len(local_coor_table):
            with open(app.config.get('COORD_TABLE_PATH'), 'w') as f:
                json.dump(new_local_coor_table, f)


def init(app: Flask):
    # 创建 instance 目录
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    # 初始化数据库
    from . import db
    db.init_app(app)

    if not os.path.exists(os.path.join(app.instance_path, 'jjwxc.sqlite')):
        db.init_db()

    # 复制/合并 coorTable.json
    if not os.path.exists(app.config.get('COORD_TABLE_PATH')):
        shutil.copy(
            os.path.join(app.root_path, 'font_parser/assets/coorTable.json'),
            app.config.get('COORD_TABLE_PATH')
        )
    else:
        try:
            merge_and_deduplicate_coor_table(app)
        except json.decoder.JSONDecodeError:
            shutil.copy(
                os.path.join(app.root_path, 'font_parser/assets/coorTable.json'),
                app.config.get('COORD_TABLE_PATH')
            )
