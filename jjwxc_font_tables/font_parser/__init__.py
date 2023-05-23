import io
import json
import os.path
import re
from copy import deepcopy
from typing import Union

import sqlalchemy as sa
import sqlalchemy.exc as sa_exc
from flask import current_app, Flask

from . import commonly_used_character
from . import download
from . import exception
from . import quick
from . import slow
from ..db import db, Font
from ..lib import (
    load_jjwxc_std_font_coord_table, deduplicate_coor_table
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
                    with io.BytesIO(font.get('bytes')) as font_fd:
                        slow_table = slow.match_jjwxc_font_one_character(x, font_fd)
                    table[x] = slow_table[x]

                    # 更新本地 coor table
                    local_coor_table = load_jjwxc_std_font_coord_table()
                    new_local_coor_table = [*local_coor_table,
                                            [slow_table[x],
                                             quick.get_character_coor_table_from_font(x, font.get('ttf'))]]

                    new_local_coor_table = deduplicate_coor_table(new_local_coor_table)
                    with open(current_app.config.get('COORD_TABLE_PATH'), 'w') as f:
                        json.dump(new_local_coor_table, f)

                    load_jjwxc_std_font_coord_table.cache_clear()

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


def init_app(app: Flask):
    font_dict = {
        "Source Han Sans SC Normal": slow.load_SourceHanSansSC_Normal(),
        "Source Han Sans SC Regular": slow.load_SourceHanSansSC_Regular()
    }
    npz_path_dict = {
        "Source Han Sans SC Normal": current_app.config.get('SOURCE_HAN_SANS_SC_NORMAL_NPZ_PATH'),
        "Source Han Sans SC Regular": current_app.config.get('SOURCE_HAN_SANS_SC_REGULARL_NPZ_PATH')
    }
    josn_path_dict = {
        "Source Han Sans SC Normal": current_app.config.get('SOURCE_HAN_SANS_SC_NORMAL_JSON_PATH'),
        "Source Han Sans SC Regular": current_app.config.get('SOURCE_HAN_SANS_SC_REGULARL_JSON_PATH')
    }

    def check(std_font_name: str) -> bool:
        guest_range = list({*slow.load_jjwxc_std_guest_range(), *commonly_used_character.character_list})

        npz_path = npz_path_dict.get(std_font_name)
        josn_path = josn_path_dict.get(std_font_name)

        if (not os.path.exists(npz_path)) or (not os.path.exists(josn_path)):
            return False

        try:
            std_im_np_arrays = slow.load_std_im_np_arrays(npz_path)
            std_im_black_point_rates = slow.load_std_im_black_point_rates(josn_path)

            for k in guest_range:
                if std_im_np_arrays.get(k) is None:
                    return False
                if std_im_black_point_rates.get(k) is None:
                    return False
        except:
            return False

        return True

    def update(std_font_name: str):
        current_app.logger.info('update cache of font {}'.format(font_name))
        font = font_dict.get(std_font_name)
        npz_path = npz_path_dict.get(std_font_name)
        josn_path = josn_path_dict.get(std_font_name)

        slow.save_std_im_np_arrays(font, npz_path)
        slow.save_std_im_black_point_rates(font, josn_path)

    for font_name in font_dict.keys():
        if not check(font_name):
            update(font_name)
