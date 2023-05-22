import collections
import json
from datetime import datetime
from typing import Optional

import click
import sqlalchemy as sa
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator

db = SQLAlchemy()


class JSONEncodedSortedOrderedDict(TypeDecorator):
    impl = sa.Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = collections.OrderedDict(sorted(value.items()))
            value = json.dumps(value)
        return value

    def process_result_value(self, value: Optional, dialect):
        if value is not None:
            value = json.loads(value)
            value = collections.OrderedDict(sorted(value.items()))
        return value


class Font(db.Model):
    __tablename__ = "fonts"
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.Text, unique=True, nullable=False)
    bytes = sa.Column(sa.BLOB, nullable=False)
    hashsum = sa.Column(sa.Text, nullable=False)
    table = sa.Column(JSONEncodedSortedOrderedDict(), nullable=False)
    created = sa.Column(sa.DateTime, nullable=False, default=datetime.now())

    def to_dict(self):
        _font = {
            "name": self.name,
            "bytes": self.bytes,
            "hashsum": self.hashsum,
            "table": self.table,
        }
        return _font


def init_db():
    db.drop_all()
    db.create_all()
    current_app.logger.info('init db')


@click.command('init-db')
def init_db_command():
    """清空当前数据并重新初始化数据库"""
    init_db()
    print('Initialized the database.')


def init_app(app: Flask):
    db.init_app(app)
    app.cli.add_command(init_db_command)
