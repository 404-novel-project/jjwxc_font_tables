import json
import os
from copy import deepcopy

from fontTools.ttLib import ttFont

from .exception import MatchError


def get_font_CoorTable(ttf: ttFont.TTFont):
    """输入 ttf 对象，输出相应的 coord table"""

    def list_ttf_characters(ttf: ttFont.TTFont) -> list[str]:
        """输入 ttf 对象，列出该字体所有字符"""
        return list(set(
            map(
                lambda x: chr(x),
                ttf.getBestCmap().keys()
            )
        ))

    def get_character_CoorTable_from_font(character: str, ttf: ttFont.TTFont) \
            -> list[tuple[int, int]]:
        """输入 ttf 对象及指定字符，输出该字体下该字符 coordTable"""
        cmap = ttf.getBestCmap()
        glyf_name = cmap[ord(character)]
        coord = ttf['glyf'][glyf_name].coordinates
        coord_list = list(coord)
        return coord_list

    characters = list_ttf_characters(ttf)
    font_coordTable = dict(zip(
        characters,
        map(
            lambda x: get_character_CoorTable_from_font(x, ttf),
            characters
        )
    ))

    return font_coordTable


def get_jjwxc_std_font_coordTable() -> dict[str, list[tuple[int, int]]]:
    """载入晋江文学城字体标准coordTable"""
    pwd = os.path.dirname(os.path.realpath(__file__))
    coordTable_path = os.path.join(pwd, 'assets/coorTable.json')
    with open(coordTable_path, 'r') as f:
        return json.load(f)


def is_glpyh_similar(a: list[tuple[int, int]], b: list[tuple[int, int]], fuzz: int):
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


def match_font(ttf: ttFont.TTFont):
    """输入晋江文学城字体对应的 ttf 对象，输出匹配后结果"""
    jjwxc_std_coordTable = get_jjwxc_std_font_coordTable()
    ttf_coordTable = get_font_CoorTable(ttf)

    # 移除晋江文学城字体 X 字符
    _ttf_coordTable = deepcopy(ttf_coordTable)
    _ttf_coordTable.pop('x', None)

    out = {}

    FUZZ = 20
    for jj_std_item in jjwxc_std_coordTable.items():
        for ttf_item in _ttf_coordTable.items():
            if is_glpyh_similar(jj_std_item[1], ttf_item[1], FUZZ):
                out[ttf_item[0]] = jj_std_item[0]
                break

    if len(_ttf_coordTable) == len(out):
        return out
    else:
        raise MatchError('快速匹配部分晋江字符失败！')
