import math
from functools import lru_cache
from typing import IO

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from flask import current_app
from fontTools.ttLib import ttFont

from .commonly_used_character import character_list
from .exception import ImageMatchError
from .quick import list_ttf_characters
from ..lib import get_jjwxc_std_font_coord_table

# 默认字号 32 px
# 行高 1.2 倍
FONT_SIZE = 96
IMAGE_SIZE = (math.ceil(FONT_SIZE * 1.2), math.ceil(FONT_SIZE * 1.2))


@lru_cache
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


def compare_im_pil(test_im: Image, std_im: Image):
    """比较两二值化图像相似度"""
    if test_im.mode != '1' or std_im.mode != '1':
        raise ImageMatchError("输入图像非二值化图像")
    if test_im.size != std_im.size:
        raise ImageMatchError("图像大小不一致")

    w, h = test_im.size
    test_black_pixel = 0
    match_pixel = 0
    for x in range(w):
        for y in range(h):
            if test_im.getpixel((x, y)) == 0:
                test_black_pixel = test_black_pixel + 1
                if test_im.getpixel((x, y)) == std_im.getpixel((x, y)):
                    match_pixel = match_pixel + 1

    return match_pixel / test_black_pixel


def compare_im_np(test_array: np.ndarray, std_array: np.ndarray):
    if test_array.shape != std_array.shape:
        raise ImageMatchError("图像大小不一致")

    test_black_array = test_array == False
    std_black_array = std_array == False
    common_black_array = test_black_array & std_black_array

    return np.count_nonzero(common_black_array) / np.count_nonzero(test_black_array)


def match_test_im(test_im: Image, std_font: ImageFont.FreeTypeFont, guest_range: list[str]):
    test_array = np.asarray(test_im)

    match_result = {}

    most_match_rate: float = 0.0
    most_match: str = ''
    for text in guest_range:
        std_im = draw(text, std_font)

        std_array = np.asarray(std_im)
        match_rate = compare_im_np(test_array, std_array)

        match_result[text] = match_rate

        if match_rate > most_match_rate:
            most_match = text
            most_match_rate = match_rate

    return most_match, match_result


def match_test_im_with_cache(test_im: Image, std_font: ImageFont.FreeTypeFont, guest_range: list[str]):
    test_array = np.asarray(test_im)

    npz_path_dict = {
        "Source Han Sans SC Normal": current_app.config.get('SOURCE_HAN_SANS_SC_NORMAL_NPZ_PATH'),
        "Source Han Sans SC Regular": current_app.config.get('SOURCE_HAN_SANS_SC_REGULARL_NPZ_PATH')
    }
    npz_path = npz_path_dict.get(' '.join(std_font.getname())) \
               or current_app.config.get('SOURCE_HAN_SANS_SC_NORMAL_NPZ_PATH')

    std_im_np_arrays = load_std_im_np_arrays(npz_path)

    match_result = {}

    most_match_rate: float = 0.0
    most_match: str = ''
    for text in guest_range:
        std_array = std_im_np_arrays[text]
        match_rate = compare_im_np(test_array, std_array)

        match_result[text] = match_rate

        if match_rate > most_match_rate:
            most_match = text
            most_match_rate = match_rate

    return most_match, match_result


def save_std_im_np_arrays(std_font: ImageFont.FreeTypeFont, npz_path: str):
    guest_range = list({*load_jjwxc_std_guest_range(), *character_list})

    npz_dict = {}

    for text in guest_range:
        std_im = draw(text, std_font)
        std_array = np.asarray(std_im)
        npz_dict[text] = std_array

    np.savez(npz_path, **npz_dict)


@lru_cache
def load_std_im_np_arrays(npz_path: str):
    return np.load(npz_path)


def match_font(test_font: ImageFont.FreeTypeFont, test_font_characters: list[str],
               std_font: ImageFont.FreeTypeFont, guest_range: list[str]):
    out = {}
    for test_char in test_font_characters:
        test_im = draw(test_char, test_font)
        most_match_char, test_match_result = match_test_im_with_cache(test_im, std_font, guest_range)
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
