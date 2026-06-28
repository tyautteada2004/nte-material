"""Neverness to Everness の静的ゲームデータ（必要数の表・素材名）。

数値は全キャラ共通。キャラごとに変わるのは「どの素材を使うか（種類）」だけ。
- 最大レベル突破: 本体育成素材 + 異象狩り素材
- スキルレベル(通常攻撃/スキル/EX終結/サポートスキル): カード + 本体育成素材 + 異象巡礼
  - サポートスキルには1度だけ開放する追加パッシブが2つ
- 弧盤突破: 弧盤育成素材 + 専用素材
  （弧盤の育成素材ラインは本体と独立して選べる＝モチーフ以外を装備し得るため）

ビートルコイン・Fons・Dreamless Seeds は集計対象外（除外/保留）。
出典: oslink / lootbar / GameWith（ナナリ）, 数値は複数キャラで相互検証済み。
"""

from __future__ import annotations

# レア度キー（緑 < 青 < 紫）
G, B, P = "緑", "青", "紫"
RARITIES = (G, B, P)

# ------------------------------------------------------------- 素材の選択肢

# 育成素材ライン（4種）。本体・弧盤の両方がこの中から1ラインを選ぶ。
IKUSEI_LINES: dict[str, dict[str, str]] = {
    "呟き": {P: "でたらめな呟き", B: "ボソボソした呟き", G: "失われし呟き"},
    "姿": {P: "仄暗い姿", B: "ぼやけた姿", G: "色褪せた姿"},
    "数字記号": {P: "歪んだ数字記号", B: "未解明の数字記号", G: "ぼやけた数字記号"},
    "ファントム": {P: "超越ファントム", B: "思想ファントム", G: "妄想ファントム"},
}

# 異象狩り素材（6種・単一素材）。最大レベル突破で消費。
HUNT_MATERIALS: tuple[str, ...] = (
    "ナイトプラグ装填",
    "海の涙",
    "妄想の向こうのワンページ",
    "語らいの花種",
    "巣籠りの残片",
    "水月色のピック",
)

# カード「フディニのトリックステージ」（5行・レア度3つ組）。スキルで消費。
CARD_ROWS: dict[str, dict[str, str]] = {
    "オリーブの枝系": {P: "オリーブの枝", B: "ハトの羽ばたき", G: "ひな鳥の願い"},
    "白薔薇系": {P: "白薔薇", B: "尉官の慎重さ", G: "新兵の臆病"},
    "ブラックハット系": {P: "ブラックハット", B: "既知の倦怠", G: "初めての期待"},
    "ドキドキナイト系": {P: "ドキドキナイト", B: "信仰の共鳴", G: "思考の同調"},
    "二人目の人系": {P: "二人目の人", B: "逆さづりの響き", G: "水波の躊躇"},
}

# 異象巡礼（3種・単一素材）。スキルの後半段階で消費。
PILGRIMAGE_MATERIALS: tuple[str, ...] = (
    "ワンワンスタンプ",
    "誇らしげな裳裾",
    "記憶の固執",
)

# 専用素材「バブル缶工場」（5行・レア度3つ組）。弧盤突破で消費。
ARC_SPECIAL_ROWS: dict[str, dict[str, str]] = {
    "リンゴの芯系": {P: "金リンゴの芯", B: "銀リンゴの芯", G: "鉄リンゴの芯"},
    "冷たいデザート系": {
        P: "冷たいデザート(特製)", B: "冷たいデザート(オリジナル)", G: "冷たいデザート(無味)"
    },
    "渦音符系": {P: "渦音符の合奏", B: "渦音符の小節", G: "渦音符の欠片"},
    "リキッドドリーム系": {
        P: "リキッドドリーム・缶入り",
        B: "リキッドドリーム・トラベルセット",
        G: "リキッドドリーム・サンプル",
    },
    "シアターチップ系": {
        P: "シアターチップ(コレクター)", B: "シアターチップ(マスター)", G: "シアターチップ(入門)"
    },
}

# ------------------------------------------------------------- レベル・必要数

# 最大レベル / 弧盤レベルのドロップダウン候補（現在の上限）
LEVEL_OPTIONS: tuple[int, ...] = (20, 30, 40, 50, 60, 70, 80)

# スキル4種
SKILLS: tuple[str, ...] = ("通常攻撃", "スキル", "EX終結", "サポートスキル")
SKILL_MAX = 10  # スキルは Lv1→10

# 最大レベル突破（from-cap -> 消費）。cap>=現在の上限 のステップが残り。
# ("育成素材", レア度, 個数) / "異象狩り" 個数
ASCENSION: dict[int, dict] = {
    20: {"ikusei": (G, 5), "hunt": 0},
    30: {"ikusei": (G, 12), "hunt": 2},
    40: {"ikusei": (B, 6), "hunt": 8},
    50: {"ikusei": (B, 12), "hunt": 16},
    60: {"ikusei": (P, 6), "hunt": 24},
    70: {"ikusei": (P, 9), "hunt": 36},
}

# 弧盤突破（from-cap -> 消費）。弧盤育成素材 + 専用素材。
ARC: dict[int, dict] = {
    20: {"ikusei": (G, 4), "special": (G, 4)},
    30: {"ikusei": (G, 10), "special": (G, 10)},
    40: {"ikusei": (B, 6), "special": (B, 6)},
    50: {"ikusei": (B, 12), "special": (B, 12)},
    60: {"ikusei": (P, 6), "special": (P, 6)},
    70: {"ikusei": (P, 12), "special": (P, 12)},
}

# スキル1段階（to-level -> 消費）。to-level>現在Lv のステップが残り。1スキル分。
SKILL_STEPS: dict[int, dict] = {
    2: {"card": (G, 2), "ikusei": (G, 2)},
    3: {"card": (G, 3), "ikusei": (G, 3)},
    4: {"card": (G, 5), "ikusei": (G, 5)},
    5: {"card": (B, 2), "ikusei": (B, 2)},
    6: {"card": (B, 3), "ikusei": (B, 3)},
    7: {"card": (B, 5), "ikusei": (B, 5), "pilgrimage": 1},
    8: {"card": (P, 3), "ikusei": (P, 3), "pilgrimage": 1},
    9: {"card": (P, 5), "ikusei": (P, 5), "pilgrimage": 2},
    10: {"card": (P, 8), "ikusei": (P, 8), "pilgrimage": 4},
}

# サポートスキルの追加パッシブ（1度開放で完了）。カード + 異象巡礼のみ。
SUPPORT_PASSIVES: dict[str, dict] = {
    "追加パッシブ1": {"card": (B, 2), "pilgrimage": 1},
    "追加パッシブ2": {"card": (P, 1), "pilgrimage": 2},
}

# 下位3つで上位1つにアップグレードできる（緑3→青1, 青3→紫1）
UPGRADE_RATIO = 3


def material_families() -> list[tuple[str, str, str]]:
    """レア度変換できる素材ファミリーの一覧。各要素は (緑, 青, 紫) の3つ組。"""
    fams: list[tuple[str, str, str]] = []
    for src in (IKUSEI_LINES, CARD_ROWS, ARC_SPECIAL_ROWS):
        for row in src.values():
            fams.append((row[G], row[B], row[P]))
    return fams


def all_materials() -> list[str]:
    """ゲーム内で登場し得る全素材名（重複なし・安定順）。所持リスト初期表示用。"""
    names: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        if name not in seen:
            seen.add(name)
            names.append(name)

    for line in IKUSEI_LINES.values():
        for r in RARITIES:
            add(line[r])
    for m in HUNT_MATERIALS:
        add(m)
    for row in CARD_ROWS.values():
        for r in RARITIES:
            add(row[r])
    for m in PILGRIMAGE_MATERIALS:
        add(m)
    for row in ARC_SPECIAL_ROWS.values():
        for r in RARITIES:
            add(row[r])
    return names


# 表示用の素材カテゴリ（同一カテゴリを隣接させる単位）
_HIGH_TO_LOW = (P, B, G)  # 高レア → 低レア


def display_order() -> list[str]:
    """集計・一覧の表示順。

    素材カテゴリ（育成素材→異象狩り→カード→異象巡礼→専用素材）ごとにまとめ、
    レア度つきは高レア→低レア（紫→青→緑）で並べる。
    """
    order: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        if name not in seen:
            seen.add(name)
            order.append(name)

    for line in IKUSEI_LINES.values():
        for r in _HIGH_TO_LOW:
            add(line[r])
    for m in HUNT_MATERIALS:
        add(m)
    for row in CARD_ROWS.values():
        for r in _HIGH_TO_LOW:
            add(row[r])
    for m in PILGRIMAGE_MATERIALS:
        add(m)
    for row in ARC_SPECIAL_ROWS.values():
        for r in _HIGH_TO_LOW:
            add(row[r])
    return order


_DISPLAY_RANK = {name: i for i, name in enumerate(display_order())}


def sort_key(name: str):
    """表示順ソート用キー。既知素材は定義順、未知（カスタム）は末尾に名前順。"""
    return (_DISPLAY_RANK.get(name, len(_DISPLAY_RANK)), name)


# 既定の選択（新規キャラ作成時）
DEFAULT_IKUSEI_LINE = next(iter(IKUSEI_LINES))
DEFAULT_HUNT = HUNT_MATERIALS[0]
DEFAULT_CARD_ROW = next(iter(CARD_ROWS))
DEFAULT_PILGRIMAGE = PILGRIMAGE_MATERIALS[0]
DEFAULT_ARC_SPECIAL_ROW = next(iter(ARC_SPECIAL_ROWS))
