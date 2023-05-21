import os
import tempfile

import pytest

from jjwxc_font_tables import create_app
from jjwxc_font_tables.db import init_db


@pytest.fixture
def app():
    db_path = tempfile.mktemp()

    app = create_app({
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///{}'.format(db_path),
        'TESTING': True,
    })

    with app.app_context():
        init_db()

    yield app

    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
