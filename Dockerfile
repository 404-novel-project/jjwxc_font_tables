FROM pypy:latest

WORKDIR /app

COPY entrypoint.sh pyproject.toml poetry.lock /app/

RUN pypy3 -m pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --without=test --no-interaction --no-ansi \
    && mkdir instance jjwxc_font_tables \
    && chmod +x /app/entrypoint.sh

ADD jjwxc_font_tables /app/jjwxc_font_tables/

EXPOSE 8080/tcp
VOLUME /app/instance
ENTRYPOINT ["/app/entrypoint.sh"]
HEALTHCHECK --interval=5m CMD curl -sf http://127.0.0.1:8080/healthcheck || exit 1