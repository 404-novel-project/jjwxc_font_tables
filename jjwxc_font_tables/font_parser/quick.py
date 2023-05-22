import json
from copy import deepcopy

from flask import current_app
from fontTools.ttLib import ttFont

from .exception import MatchError


def list_ttf_characters(ttf: ttFont.TTFont) -> list[str]:
    """输入 ttf 对象，列出该字体所有字符"""
    return list(set(
        map(
            lambda x: chr(x),
            ttf.getBestCmap().keys()
        )
    ))


def get_character_coor_table_from_font(character: str, ttf: ttFont.TTFont) \
        -> list[tuple[int, int]]:
    """输入 ttf 对象及指定字符，输出该字体下该字符 coordTable"""
    cmap = ttf.getBestCmap()
    glyf_name = cmap[ord(character)]
    coord = ttf['glyf'][glyf_name].coordinates
    coord_list = list(coord)
    return coord_list


def get_font_coor_table(ttf: ttFont.TTFont) -> dict[str, list[tuple[int, int]]]:
    """输入 ttf 对象，输出相应的 coord table"""
    characters = list_ttf_characters(ttf)
    font_coord_table = dict(zip(
        characters,
        map(
            lambda x: get_character_coor_table_from_font(x, ttf),
            characters
        )
    ))

    return font_coord_table


def get_jjwxc_std_font_coord_table() -> list[
    tuple[
        str,
        list[tuple[int, int]]
    ]
]:
    """载入晋江文学城字体标准coordTable"""
    with open(current_app.config.get('COORD_TABLE_PATH'), 'r') as f:
        _t = json.load(f)
        return sorted(_t, key=lambda x: x[0])


def is_glpyh_similar(a: list[tuple[int, int]], b: list[tuple[int, int]], fuzz: int) -> bool:
    """
    比较两字符 coor 是否相似。
    来自：https://github.com/fffonion/JJGet/blob/master/scripts/generate_font.py#L37-L45
    """
    if len(a) != len(b):
        return False
    found = True
    for ii in range(len(a)):
        if abs(a[ii][0] - b[ii][0]) > fuzz or abs(a[ii][1] - b[ii][1]) > fuzz:
            found = False
            break
    return found


def match_font(ttf: ttFont.TTFont) -> dict[str, str]:
    """输入晋江文学城字体对应的 ttf 对象，输出匹配后结果"""
    jjwxc_std_coord_table = get_jjwxc_std_font_coord_table()
    ttf_coord_table = get_font_coor_table(ttf)

    # 移除晋江文学城字体 X 字符
    _ttf_coordTable = deepcopy(ttf_coord_table)
    _ttf_coordTable.pop('x', None)

    out = {}

    # noinspection PyPep8Naming
    FUZZ = 20
    for jj_std_item in jjwxc_std_coord_table:
        for ttf_item in _ttf_coordTable.items():
            if is_glpyh_similar(jj_std_item[1], ttf_item[1], FUZZ):
                out[ttf_item[0]] = jj_std_item[0]
                break

    if len(_ttf_coordTable) == len(out):
        return out
    else:
        raise MatchError('快速匹配部分晋江字符失败！')
