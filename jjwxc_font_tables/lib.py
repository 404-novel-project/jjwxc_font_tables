import copy
import hashlib
import json

from flask import Response


def add_etag(response: Response):
    m = hashlib.sha1()
    m.update(response.data)
    response.set_etag(m.hexdigest())


def get_charater_hex(chac: str):
    return str(hex(ord(chac))).replace('0x', 'U+')


def get_jjwxc_std_font_coord_table() -> list[
    tuple[
        str,
        list[tuple[int, int]]
    ]
]:
    """载入晋江文学城字体标准coordTable"""
    from flask import current_app

    with open(current_app.config.get('COORD_TABLE_PATH'), 'r') as f:
        _t = json.load(f)
        return sorted(_t, key=lambda x: x[0])


def is_coor_match(x, y) -> bool:
    """比较 coor"""

    # 如果字符 coor 长度相同
    if len(x) == len(y):
        match = True
        # 逐一比较各点
        for ii in range(len(x)):
            rx, ry = x[ii]
            lx, ly = y[ii]
            if rx != lx or ry != ly:
                match = False
                break
        return match
    else:
        return False


def merge_coor_table(source, target):
    source_copy = copy.copy(source)
    for j in source:
        for k in target:
            if j[0] == k[0] and is_coor_match(j[1], k[1]):
                source_copy.remove(j)
    return sorted([*target, *source_copy], key=lambda x: x[0])


def deduplicate_coor_table(source: list):
    rm_list = []
    source_length = len(source)
    for j in range(source_length):
        for k in range(source_length):
            if j > k and \
                    source[j][0] == source[k][0] and is_coor_match(source[j][1], source[k][1]):
                if k not in rm_list:
                    rm_list.append(k)

    target = []
    for index, value in enumerate(source):
        if index not in rm_list:
            target.append(value)

    return target
