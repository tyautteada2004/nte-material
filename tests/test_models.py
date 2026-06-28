"""モデルと集計ロジックのテスト。

    python tests/test_models.py     （追加ライブラリ不要）
    python -m pytest                （pytest があれば）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nte_material import gamedata as gd
from nte_material.models import Character, Project


def _chaos() -> Character:
    """カオス相当の選択（検証用）。"""
    ch = Character.new("カオス")
    ch.ikusei_line = "ファントム"
    ch.arc_ikusei_line = "ファントム"
    ch.hunt_mat = "海の涙"
    ch.card_row = "ドキドキナイト系"
    ch.pilgrimage_mat = "記憶の固執"
    ch.arc_special_row = "冷たいデザート系"
    return ch


def test_ascension_full_matches_known_totals():
    """最大Lv20→80（全突破）の合計が判明値と一致。"""
    ch = _chaos()
    ch.ascension_level = 20
    # 集計に最大レベルだけ出したいので他を完了状態に
    ch.include_arc = False
    for sk in ch.skill_levels:
        ch.skill_levels[sk] = gd.SKILL_MAX
    for k in ch.support_done:
        ch.support_done[k] = True
    rem = ch.remaining()
    # 育成素材(ファントム): 緑17/青18/紫15、異象狩り(海の涙)86
    assert rem["妄想ファントム"] == 17
    assert rem["思想ファントム"] == 18
    assert rem["超越ファントム"] == 15
    assert rem["海の涙"] == 86


def test_ascension_level_reduces_remaining():
    ch = _chaos()
    ch.include_arc = False
    for sk in ch.skill_levels:
        ch.skill_levels[sk] = gd.SKILL_MAX
    for k in ch.support_done:
        ch.support_done[k] = True
    ch.ascension_level = 60  # 残りは cap60,70 のみ
    rem = ch.remaining()
    assert rem.get("超越ファントム") == 6 + 9   # 紫: 6+9
    assert rem.get("海の涙") == 24 + 36
    assert "妄想ファントム" not in rem          # 緑は60未満で完了済み
    ch.ascension_level = 80                      # 完了 → 最大Lv由来はゼロ
    assert ch.remaining() == {}


def test_skill_totals_reconcile_with_known_values():
    """4スキル満凸＋サポート2パッシブの合計が判明値と一致。"""
    ch = _chaos()
    ch.ascension_level = 80
    ch.include_arc = False
    rem = ch.remaining()
    card = gd.CARD_ROWS["ドキドキナイト系"]
    # カード: 緑40 / 青42 / 紫65、巡礼35、育成素材 緑40/青40/紫64
    assert rem[card["緑"]] == 40
    assert rem[card["青"]] == 42
    assert rem[card["紫"]] == 65
    assert rem["記憶の固執"] == 35
    assert rem["妄想ファントム"] == 40
    assert rem["思想ファントム"] == 40
    assert rem["超越ファントム"] == 64


def test_arc_independent_ikusei_line():
    """弧盤の育成素材ラインは本体と独立して集計される。"""
    ch = _chaos()
    ch.ascension_level = 80
    for sk in ch.skill_levels:
        ch.skill_levels[sk] = gd.SKILL_MAX
    for k in ch.support_done:
        ch.support_done[k] = True
    ch.arc_ikusei_line = "呟き"      # 本体=ファントム とは別ライン
    ch.arc_level = 20
    rem = ch.remaining()
    # 弧盤育成素材(呟き) 緑14/青18/紫18、専用素材(デザート) 緑14/青18/紫18
    assert rem["失われし呟き"] == 14
    assert rem["ボソボソした呟き"] == 18
    assert rem["でたらめな呟き"] == 18
    assert rem["冷たいデザート(無味)"] == 14
    assert rem["冷たいデザート(特製)"] == 18


def test_project_total_and_roundtrip():
    proj = Project()
    a = _chaos()
    a.ascension_level = 80
    a.include_arc = False
    for sk in a.skill_levels:
        a.skill_levels[sk] = gd.SKILL_MAX
    a.support_done["追加パッシブ1"] = True
    a.support_done["追加パッシブ2"] = False  # 紫カード1 + 巡礼2 残り
    proj.characters = [a]
    rem = proj.total_remaining()
    assert rem[gd.CARD_ROWS["ドキドキナイト系"]["紫"]] == 1
    assert rem["記憶の固執"] == 2
    # JSON 往復で集計不変
    restored = Project.from_dict(proj.to_dict())
    assert restored.total_remaining() == rem


def test_inventory_set_adjust_and_shortage():
    proj = Project()
    a = _chaos()
    a.ascension_level = 80
    a.include_arc = False
    a.support_done["追加パッシブ1"] = True
    a.support_done["追加パッシブ2"] = True
    for sk in a.skill_levels:
        a.skill_levels[sk] = 9  # Lv10 ぶんだけ残す
    proj.characters = [a]

    card_p = gd.CARD_ROWS["ドキドキナイト系"]["紫"]
    rem = proj.total_remaining()[card_p]      # Lv10×4スキル = 紫8×4 = 32
    assert rem == 32

    proj.set_owned(card_p, 10)
    proj.adjust_owned(card_p, +5)             # 15
    proj.adjust_owned(card_p, -100)           # 0未満は0に丸め
    assert proj.owned(card_p) == 0
    proj.set_owned(card_p, 20)

    by_name = {n: (r, o, s) for n, r, o, s in proj.material_rows()}
    assert by_name[card_p] == (32, 20, 12)    # 不足 = 32-20

    # 所持が残りを上回れば不足0
    proj.set_owned(card_p, 50)
    by_name = {n: (r, o, s) for n, r, o, s in proj.material_rows()}
    assert by_name[card_p][2] == 0

    # 在庫つき JSON 往復
    restored = Project.from_dict(proj.to_dict())
    assert restored.owned(card_p) == 50


def test_inventory_custom_material_and_delete():
    proj = Project()
    proj.set_owned("自作素材", 7)
    names = {n for n, *_ in proj.material_rows()}
    assert "自作素材" in names
    proj.remove_material("自作素材")
    names = {n for n, *_ in proj.material_rows()}
    assert "自作素材" not in names


def test_display_order_groups_category_and_high_to_low_rarity():
    order = gd.display_order()
    idx = {name: i for i, name in enumerate(order)}

    # 同一ライン内は 紫 → 青 → 緑
    line = gd.IKUSEI_LINES["ファントム"]
    assert idx[line["紫"]] < idx[line["青"]] < idx[line["緑"]]
    card = gd.CARD_ROWS["ドキドキナイト系"]
    assert idx[card["紫"]] < idx[card["青"]] < idx[card["緑"]]

    # 育成素材カテゴリは専用素材カテゴリより前にまとまる
    last_ikusei = max(idx[gd.IKUSEI_LINES[ln][r]] for ln in gd.IKUSEI_LINES for r in gd.RARITIES)
    first_special = min(
        idx[gd.ARC_SPECIAL_ROWS[rw][r]] for rw in gd.ARC_SPECIAL_ROWS for r in gd.RARITIES
    )
    assert last_ikusei < first_special

    # カスタム素材は末尾
    assert gd.sort_key("未知の素材")[0] == len(order)


def test_material_rows_follow_display_order():
    proj = Project()
    proj.characters = [_chaos()]
    names = [n for n, *_ in proj.material_rows()]
    ranks = [gd.sort_key(n)[0] for n in names]
    assert ranks == sorted(ranks)  # display_order 準拠で単調増加


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} passed")


if __name__ == "__main__":
    _run_all()
