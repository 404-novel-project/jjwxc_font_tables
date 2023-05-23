import io
import json
import tempfile
import time
from typing import Union
from uuid import uuid4

from flask import g, current_app, render_template
from fontTools.ttLib import ttFont, TTLibError, woff2
from werkzeug.utils import secure_filename

from .commonly_used_character import character_list
from .download import get_font
from .quick import list_ttf_characters
from .slow import (
    load_SourceHanSansSC_Normal, load_SourceHanSansSC_Regular, load_jjwxc_std_guest_range, match_jjwxc_font, match_font,
    _load_font
)
from ..lib import get_charater_hex


async def match_jjwxc_font_tool(font_name: str, options=None) -> Union[tuple[str, int], tuple[None, int]]:
    font = await get_font(font_name)
    status = font.get('status')

    if status == 'OK':
        if options is None:
            options = {
                "std_font": "SourceHanSansSC-Normal",
                "guest_range": "jjwxc"
            }

        std_font_dict = {
            "SourceHanSansSC-Normal": load_SourceHanSansSC_Normal(),
            "SourceHanSansSC-Regular": load_SourceHanSansSC_Regular()
        }
        guest_range_dict = {
            "jjwxc": load_jjwxc_std_guest_range(),
            "2500": character_list
        }
        std_font = std_font_dict.get(
            options.get('std_font') or "SourceHanSansSC-Normal"
        ) or load_SourceHanSansSC_Normal()
        guest_range = guest_range_dict.get(
            options.get('guest_range') or "jjwxc"
        ) or load_jjwxc_std_guest_range()

        g.uuid = uuid4()
        current_app.logger.info(
            "match_jjwxc_font_tools start: {uuid} {fontname} {options}".format(
                uuid=g.uuid, fontname=font.get('name'), options=json.dumps(options)
            )
        )
        T1 = time.perf_counter()

        with io.BytesIO(font.get('bytes')) as font_fd:
            table = match_jjwxc_font(
                font_fd, font.get('ttf'),
                std_font, guest_range
            )

        T2 = time.perf_counter()
        current_app.logger.info(
            "match_jjwxc_font_tools finished: {uuid} {cost_time}ms".format(
                uuid=g.uuid, fontname=font.get('name'), cost_time=(T2 - T1) * 1000
            )
        )
        return render_template('font.html', font={"name": font.get('name'), "table": table},
                               get_charater_hex=get_charater_hex), 200
    elif status == "404":
        return None, 404
    else:
        return None, 503


async def match_upload_font_tool(
        upload_font_filename: str, upload_font_bytes: bytes, upload_font_mimetype: str,
        options=None
) -> Union[tuple[str, int], tuple[None, int]]:
    fontname = secure_filename(upload_font_filename)

    if options is None:
        options = {
            "std_font": "SourceHanSansSC-Normal",
            "guest_range": "jjwxc"
        }

    std_font_dict = {
        "SourceHanSansSC-Normal": load_SourceHanSansSC_Normal(),
        "SourceHanSansSC-Regular": load_SourceHanSansSC_Regular()
    }
    guest_range_dict = {
        "jjwxc": load_jjwxc_std_guest_range(),
        "2500": character_list
    }
    std_font = std_font_dict.get(
        options.get('std_font') or "SourceHanSansSC-Normal"
    ) or load_SourceHanSansSC_Normal()
    guest_range = guest_range_dict.get(
        options.get('guest_range') or "jjwxc"
    ) or load_jjwxc_std_guest_range()

    with io.BytesIO(upload_font_bytes) as font_fd:
        try:
            ttf_ttFont = ttFont.TTFont(font_fd)
            font_fd.seek(0)
            ttf_ImageFont = _load_font(font_fd)
        except TTLibError:
            try:
                with tempfile.TemporaryFile() as tmp:
                    font_fd.seek(0)
                    woff2.decompress(font_fd, tmp)
                    font_fd.seek(0)
                    tmp.seek(0)
                    ttf_ttFont = ttFont.TTFont(tmp)
                    tmp.seek(0)
                    ttf_ImageFont = _load_font(tmp)
            except BaseException:
                return None, 400

    g.uuid = uuid4()
    current_app.logger.info(
        "match_upload_font_tool start: {uuid} {fontname} {options}".format(
            uuid=g.uuid, fontname=fontname, options=json.dumps(options)
        )
    )
    T1 = time.perf_counter()

    table = match_font(
        ttf_ImageFont, list_ttf_characters(ttf_ttFont),
        std_font, guest_range
    )

    T2 = time.perf_counter()
    current_app.logger.info(
        "match_upload_font_tool finished: {uuid} {cost_time}ms".format(
            uuid=g.uuid, fontname=fontname, cost_time=(T2 - T1) * 1000
        )
    )

    return render_template(
        'tools/slow_match_upload_font.html',
        font={"name": fontname, "table": table},
        get_charater_hex=get_charater_hex,
        font_url_filename=fontname,
        font_url_format=upload_font_mimetype.split('/')[-1]
    ), 200
