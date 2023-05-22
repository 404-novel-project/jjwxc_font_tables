#!/bin/bash

gunicorn --bind 0.0.0.0:8080  -w $(nproc) --preload -k gevent "jjwxc_font_tables:create_app()"