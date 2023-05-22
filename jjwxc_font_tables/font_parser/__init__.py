import re
from copy import deepcopy
from typing import Union

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc

from . import download
from . import exception
from . import quick
from ..db import db, Font


def validator(input_font_name: str) -> bool:
    if len(input_font_name) == 15 \
            and input_font_name.startswith('jjwxcfont_') \
            and re.match(r'^\w{5}$', input_font_name.replace('jjwxcfont_', '')):
        return True

    return False


async def _match(font_name: str) -> Union[tuple[None, int], tuple[dict, int]]:
    font = await download.get_font(font_name)
    status = font.get('status')
    if status == 'OK':
        try:
            table = quick.match_font(font.get('ttf'))

            out = deepcopy(font)
            out.pop('ttf', None)
            out['table'] = table

            return out, 200
        except exception.MatchError:
            # 运行慢速算法
            # TODO
            return None, 555
    elif status == "404":
        return None, 404
    else:
        return None, 502


async def match(font_name: str) -> Union[tuple[None, int], tuple[Font, int]]:
    if not validator(font_name):
        return None, 403
    try:
        return db.session.execute(
            sa.select(Font).where(Font.name.is_(font_name))
        ).scalar_one(), 200
    except (sa_exc.NoResultFound, sa_exc.MultipleResultsFound):
        _font, status_code = await _match(font_name)
        if status_code == 200:
            font = Font(
                name=_font.get('name'),
                bytes=_font.get('bytes'),
                hashsum=_font.get('hashsum'),
                table=_font.get('table')
            )
            db.session.add(font)
            db.session.commit()
            return (await match(font_name))
        else:
            return None, status_code
