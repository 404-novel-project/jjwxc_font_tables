import io
import json
import math
import time
from functools import lru_cache
from typing import IO, Union
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from flask import current_app, render_template, g
from fontTools.ttLib import ttFont

from .commonly_used_character import character_list
from .download import get_font
from .exception import ImageMatchError
from .quick import list_ttf_characters
from ..lib import get_charater_hex, get_jjwxc_std_font_coord_table

# 默认字号 32 px
# 行高 1.2 倍
FONT_SIZE = 96
IMAGE_SIZE = (math.ceil(FONT_SIZE * 1.2), math.ceil(FONT_SIZE * 1.2))


def _load_font(font, size=FONT_SIZE):
    return ImageFont.truetype(font, size=size)


def load_SourceHanSansSC_Normal() -> ImageFont.FreeTypeFont:
    return _load_font(current_app.config.get('SOURCE_HAN_SANS_SC_NORMAL_PATH'))


def load_SourceHanSansSC_Regular() -> ImageFont.FreeTypeFont:
    return _load_font(current_app.config.get('SOURCE_HAN_SANS_SC_REGULAR_PATH'))


def load_jjwxc_std_guest_range() -> list[str]:
    return list(set(
        filter(
            lambda x: x != 'x',
            map(
                lambda x: x[0],
                get_jjwxc_std_font_coord_table()
            ))
    ))


def _get_offset(im: Image, font: ImageFont.FreeTypeFont, text: str):
    im_width, im_heigth = im.size

    # 获取文字默认位置（默认偏移）
    # https://pillow.readthedocs.io/en/stable/handbook/text-anchors.html
    # https://pillow.readthedocs.io/en/stable/reference/ImageFont.html#PIL.ImageFont.FreeTypeFont.getbbox
    text_bbox = font.getbbox(text)

    text_width = font.getlength(text)
    text_height = text_bbox[3] - text_bbox[1]

    # 使文字居中理论偏移量
    _offset_x = (im_width - text_width) / 2
    _offset_y = (im_heigth - text_height) / 2

    # 计算所需偏移
    offset_x = _offset_x - text_bbox[0]
    offset_y = _offset_y - text_bbox[1]
    return offset_x, offset_y


@lru_cache(maxsize=3500)
def draw(text: str, font: ImageFont.FreeTypeFont, size: tuple[int, int] = IMAGE_SIZE):
    image = Image.new("1", size, "white")
    d = ImageDraw.Draw(image)
    d.text(_get_offset(image, font, text), text, font=font, fill="black")
    return image


def compare_im(im_x: Image, im_y: Image):
    """比较两二值化图像相似度"""
    if im_x.size[0] != im_y.size[0] or im_x.size[1] != im_y.size[1]:
        raise ImageMatchError("图像大小不一致")
    if im_x.mode != '1' or im_y.mode != '1':
        raise ImageMatchError("输入图像非二值化图像")

    w, h = im_x.size
    total_pixel = w * h
    match_pixel = 0
    for x in range(w):
        for y in range(h):
            if im_x.getpixel((x, y)) == 0 and im_x.getpixel((x, y)) == im_y.getpixel((x, y)):
                match_pixel = match_pixel + 1

    return match_pixel / total_pixel


def match_test_im(test_im: Image, std_font: ImageFont.FreeTypeFont, guest_range: list[str]):
    match_result = {}

    most_match_rate: float = 0.0
    most_match: str = ''
    for text in guest_range:
        std_im = draw(text, std_font)
        match_rate = compare_im(test_im, std_im)
        match_result[text] = match_rate

        if match_rate > most_match_rate:
            most_match = text
            most_match_rate = match_rate

    return most_match, match_result


def match_font(test_font: ImageFont.FreeTypeFont, test_font_characters: list[str],
               std_font: ImageFont.FreeTypeFont, guest_range: list[str]):
    out = {}
    for test_char in test_font_characters:
        test_im = draw(test_char, test_font)
        most_match_char, test_match_result = match_test_im(test_im, std_font, guest_range)
        out[test_char] = most_match_char

    return out


def match_jjwxc_font(jjwxc_font_fd: IO, jjwxc_font_ttf: ttFont.TTFont,
                     std_font=None, guest_range=None):
    jjwxc_image_font = _load_font(jjwxc_font_fd)
    jjwxc_characters = list(filter(lambda x: x != 'x', list_ttf_characters(jjwxc_font_ttf)))

    std_font = std_font or load_SourceHanSansSC_Normal()
    guest_range = guest_range or load_jjwxc_std_guest_range()

    return match_font(
        jjwxc_image_font, jjwxc_characters,
        std_font, guest_range
    )


def match_jjwxc_font_one_character(test_character: str, jjwxc_font_fd: IO,
                                   std_font=None, guest_range=None):
    jjwxc_image_font = _load_font(jjwxc_font_fd)

    std_font = std_font or load_SourceHanSansSC_Normal()
    guest_range = guest_range or load_jjwxc_std_guest_range()

    return match_font(
        jjwxc_image_font, [test_character],
        std_font, guest_range
    )


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
