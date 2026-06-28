"""アイコン補助（Tk不要部分）のテスト。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nte_material import gamedata as gd
from nte_material import icons


def test_safe_filename_replaces_forbidden_chars():
    assert icons.safe_filename("冷たいデザート(特製)") == "冷たいデザート(特製)"
    assert icons.safe_filename('a/b:c*d?"e<f>g|h\\i') == "a_b_c_d__e_f_g_h_i"


def test_rarity_map_covers_tiered_materials():
    rmap = icons._rarity_map()
    # レア度つき素材は緑/青/紫のいずれか
    assert rmap[gd.IKUSEI_LINES["ファントム"]["紫"]] == "紫"
    assert rmap[gd.CARD_ROWS["ドキドキナイト系"]["緑"]] == "緑"
    assert rmap[gd.ARC_SPECIAL_ROWS["リンゴの芯系"]["青"]] == "青"
    # 単一素材（異象狩り/巡礼）はレア度なし
    assert "海の涙" not in rmap
    assert "記憶の固執" not in rmap


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)} passed")


if __name__ == "__main__":
    _run_all()
