import io
import json
import re
import time
from copy import deepcopy
from typing import Union
from uuid import uuid4

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
from flask import current_app, g

from . import download
from . import exception
from . import quick
from . import slow
from ..db import db, Font
from ..lib import (
    get_charater_hex, get_jjwxc_std_font_coord_table, deduplicate_coor_table
)


def validator(input_font_name: str) -> bool:
    if len(input_font_name) == 15 \
            and input_font_name.startswith('jjwxcfont_') \
            and re.match(r'^\w{5}$', input_font_name.replace('jjwxcfont_', '')):
        return True

    return False


async def _match_jjwxc_font(font_name: str) -> \
        Union[
            tuple[None, int],
            tuple[dict[str, Union[str, bytes, dict[str, str]]], int]
        ]:
    font = await download.get_font(font_name)
    status = font.get('status')
    if status == 'OK':
        table, quick_match_status = quick.match_jjwxc_font(font.get('ttf'))

        if quick_match_status != "OK":
            _ttf_coordTable = quick_match_status
            for x in _ttf_coordTable:
                if x not in table.keys():
                    g.uuid = uuid4()
                    current_app.logger.info(
                        "font_parser slow_match start: {uuid} {fontname} {charater}".format(
                            uuid=g.uuid, fontname=font.get('name'), charater=get_charater_hex(x)
                        )
                    )
                    T1 = time.perf_counter()

                    with io.BytesIO(font.get('bytes')) as font_fd:
                        slow_table = slow.match_jjwxc_font_one_character(x, font_fd)
                    table[x] = slow_table[x]

                    # 更新本地 coor table
                    local_coor_table = get_jjwxc_std_font_coord_table()
                    new_local_coor_table = [*local_coor_table,
                                            [slow_table[x],
                                             quick.get_character_coor_table_from_font(x, font.get('ttf'))]]

                    new_local_coor_table = deduplicate_coor_table(new_local_coor_table)
                    with open(current_app.config.get('COORD_TABLE_PATH'), 'w') as f:
                        json.dump(new_local_coor_table, f)

                    T2 = time.perf_counter()
                    current_app.logger.info(
                        "font_parser slow_match finished: {uuid} {cost_time}ms".format(
                            uuid=g.uuid, fontname=font.get('name'), cost_time=(T2 - T1) * 1000
                        )
                    )

        out: dict[str, Union[str, bytes, dict[str, str]]] = deepcopy(font)
        out.pop('ttf', None)
        out['table'] = table
        return out, 200
    elif status == "404":
        return None, 404
    else:
        return None, 503


async def match_jjwxc_font(font_name: str) -> \
        Union[
            tuple[None, int],
            tuple[dict[str, Union[str, bytes, dict[str, str]]], int]
        ]:
    if not validator(font_name):
        return None, 403
    try:
        return db.session.execute(
            sa.select(Font).where(Font.name.is_(font_name))
        ).scalar_one(), 200
    except (sa_exc.NoResultFound, sa_exc.MultipleResultsFound):
        _font, status_code = await _match_jjwxc_font(font_name)
        if status_code == 200:
            font = Font(
                name=_font.get('name'),
                bytes=_font.get('bytes'),
                hashsum=_font.get('hashsum'),
                table=_font.get('table')
            )
            db.session.add(font)
            db.session.commit()
            return await match_jjwxc_font(font_name)
        else:
            return None, status_code
