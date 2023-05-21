import hashlib

from flask import Response


def add_etag(response: Response):
    m = hashlib.sha1()
    m.update(response.data)
    response.set_etag(m.hexdigest())
