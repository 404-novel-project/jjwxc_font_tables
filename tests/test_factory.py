import copy
import json
import os

from jjwxc_font_tables import create_app, merge_coor_table, deduplicate_coor_table


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_merge_coor_table(app):
    with open(os.path.join(app.root_path, 'font_parser/assets/coorTable.json'), 'r') as f:
        _coorTable = json.load(f)
        coor_table: list[
            tuple[
                str,
                list[tuple[int, int]]
            ]
        ] = sorted(_coorTable, key=lambda x: x[0])

    test_coor_table = copy.deepcopy(coor_table)

    rm_coor_table_list = []
    rm_coor_table_list.append(test_coor_table.pop(3))
    rm_coor_table_list.append(test_coor_table.pop())

    assert len(test_coor_table) != len(coor_table)

    test2_coor_table = merge_coor_table(coor_table, test_coor_table)

    assert len(test2_coor_table) == len(coor_table)


def test_deduplicate_coor_table(app):
    with open(os.path.join(app.root_path, 'font_parser/assets/coorTable.json'), 'r') as f:
        _coorTable = json.load(f)
        coor_table: list[
            tuple[
                str,
                list[tuple[int, int]]
            ]
        ] = sorted(_coorTable, key=lambda x: x[0])

    deduplicate_list = [coor_table[7], coor_table[0], coor_table[0], coor_table[15], coor_table[115]]
    test_coor_table = [*copy.deepcopy(coor_table), *copy.deepcopy(deduplicate_list)]

    assert len(test_coor_table) != len(coor_table)

    test2_coor_table = deduplicate_coor_table(test_coor_table)

    assert len(test2_coor_table) == len(coor_table)
