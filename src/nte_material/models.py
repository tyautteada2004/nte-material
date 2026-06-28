"""キャラの状態と、残り素材の集計ロジック。

必要数は gamedata の共通テーブルを使い、キャラごとの「素材の種類」選択で
具体名へ解決して合算する。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import gamedata as gd


def _merge(into: dict[str, int], material: str, qty: int) -> None:
    if qty:
        into[material] = into.get(material, 0) + qty


def _default_skill_levels() -> dict[str, int]:
    return {name: 1 for name in gd.SKILLS}


def _default_support() -> dict[str, bool]:
    return {name: False for name in gd.SUPPORT_PASSIVES}


@dataclass
class Character:
    """キャラ1体の選択と進捗。"""

    name: str
    # 素材の種類（キャラ依存の選択）
    ikusei_line: str = gd.DEFAULT_IKUSEI_LINE        # 本体育成素材ライン（最大Lv+スキル共通）
    arc_ikusei_line: str = gd.DEFAULT_IKUSEI_LINE    # 弧盤育成素材ライン（独立）
    hunt_mat: str = gd.DEFAULT_HUNT                   # 異象狩り素材
    card_row: str = gd.DEFAULT_CARD_ROW              # カード行
    pilgrimage_mat: str = gd.DEFAULT_PILGRIMAGE      # 異象巡礼
    arc_special_row: str = gd.DEFAULT_ARC_SPECIAL_ROW  # 専用素材行
    # 進捗
    ascension_level: int = 20                        # 現在の最大レベル（上限）
    arc_level: int = 20                              # 現在の弧盤レベル（上限）
    include_ascension: bool = True                   # 最大レベルを集計に含めるか
    include_skill: bool = True                       # スキルを集計に含めるか
    include_arc: bool = True                         # 弧盤を集計に含めるか
    skill_levels: dict[str, int] = field(default_factory=_default_skill_levels)
    support_done: dict[str, bool] = field(default_factory=_default_support)

    # ---------------------------------------------------- 残り素材の集計
    def remaining(self) -> dict[str, int]:
        out: dict[str, int] = {}
        ik = gd.IKUSEI_LINES[self.ikusei_line]
        arc_ik = gd.IKUSEI_LINES[self.arc_ikusei_line]
        card = gd.CARD_ROWS[self.card_row]
        special = gd.ARC_SPECIAL_ROWS[self.arc_special_row]

        # 最大レベル突破: 現在の上限以上のステップが残り
        if self.include_ascension:
            for cap, step in gd.ASCENSION.items():
                if cap >= self.ascension_level:
                    r, q = step["ikusei"]
                    _merge(out, ik[r], q)
                    _merge(out, self.hunt_mat, step["hunt"])

        # スキル（4種＋サポート追加パッシブ）
        if self.include_skill:
            # スキル4種: 現在Lvより上の段階が残り
            for lv in self.skill_levels.values():
                for to_lv, step in gd.SKILL_STEPS.items():
                    if to_lv > lv:
                        r, q = step["card"]
                        _merge(out, card[r], q)
                        r2, q2 = step["ikusei"]
                        _merge(out, ik[r2], q2)
                        _merge(out, self.pilgrimage_mat, step.get("pilgrimage", 0))
            # サポート追加パッシブ: 未開放なら残り
            for name, done in self.support_done.items():
                if not done:
                    step = gd.SUPPORT_PASSIVES[name]
                    r, q = step["card"]
                    _merge(out, card[r], q)
                    _merge(out, self.pilgrimage_mat, step.get("pilgrimage", 0))

        # 弧盤突破
        if self.include_arc:
            for cap, step in gd.ARC.items():
                if cap >= self.arc_level:
                    r, q = step["ikusei"]
                    _merge(out, arc_ik[r], q)
                    r2, q2 = step["special"]
                    _merge(out, special[r2], q2)

        return out

    # ---------------------------------------------------- 永続化
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ikusei_line": self.ikusei_line,
            "arc_ikusei_line": self.arc_ikusei_line,
            "hunt_mat": self.hunt_mat,
            "card_row": self.card_row,
            "pilgrimage_mat": self.pilgrimage_mat,
            "arc_special_row": self.arc_special_row,
            "ascension_level": self.ascension_level,
            "arc_level": self.arc_level,
            "include_ascension": self.include_ascension,
            "include_skill": self.include_skill,
            "include_arc": self.include_arc,
            "skill_levels": dict(self.skill_levels),
            "support_done": dict(self.support_done),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Character":
        ch = cls(name=str(d["name"]))
        ch.ikusei_line = d.get("ikusei_line", ch.ikusei_line)
        ch.arc_ikusei_line = d.get("arc_ikusei_line", ch.arc_ikusei_line)
        ch.hunt_mat = d.get("hunt_mat", ch.hunt_mat)
        ch.card_row = d.get("card_row", ch.card_row)
        ch.pilgrimage_mat = d.get("pilgrimage_mat", ch.pilgrimage_mat)
        ch.arc_special_row = d.get("arc_special_row", ch.arc_special_row)
        ch.ascension_level = int(d.get("ascension_level", ch.ascension_level))
        ch.arc_level = int(d.get("arc_level", ch.arc_level))
        ch.include_ascension = bool(d.get("include_ascension", ch.include_ascension))
        ch.include_skill = bool(d.get("include_skill", ch.include_skill))
        ch.include_arc = bool(d.get("include_arc", ch.include_arc))
        # 既知のスキル/パッシブだけ取り込む（データ破損・項目追加に強くする）
        for k in gd.SKILLS:
            ch.skill_levels[k] = int(d.get("skill_levels", {}).get(k, ch.skill_levels[k]))
        for k in gd.SUPPORT_PASSIVES:
            ch.support_done[k] = bool(d.get("support_done", {}).get(k, ch.support_done[k]))
        return ch

    @classmethod
    def new(cls, name: str) -> "Character":
        return cls(name=name)


@dataclass
class Project:
    """全キャラ＋所持リソースを束ねる最上位。"""

    characters: list[Character] = field(default_factory=list)
    inventory: dict[str, int] = field(default_factory=dict)  # 素材名 -> 所持数

    def total_remaining(self) -> dict[str, int]:
        total: dict[str, int] = {}
        for ch in self.characters:
            for material, qty in ch.remaining().items():
                total[material] = total.get(material, 0) + qty
        return total

    def material_breakdown(self, material: str) -> list[tuple[str, int]]:
        """指定素材を必要とするキャラと、その必要数の一覧（必要数の多い順）。"""
        out = [
            (ch.name, ch.remaining().get(material, 0))
            for ch in self.characters
        ]
        out = [(name, qty) for name, qty in out if qty]
        out.sort(key=lambda t: (-t[1], t[0]))
        return out

    def get_character(self, name: str) -> Character | None:
        for ch in self.characters:
            if ch.name == name:
                return ch
        return None

    # ---------------------------------------------------- 所持リソース操作
    def owned(self, material: str) -> int:
        return self.inventory.get(material, 0)

    def set_owned(self, material: str, qty: int) -> None:
        """所持数を直接書き換える（0未満は0に丸める）。"""
        self.inventory[material] = max(0, int(qty))

    def adjust_owned(self, material: str, delta: int) -> None:
        """所持数を一定数だけ増減する（0未満は0に丸める）。"""
        self.inventory[material] = max(0, self.owned(material) + int(delta))

    def remove_material(self, material: str) -> None:
        """所持リストから素材を削除する。"""
        self.inventory.pop(material, None)

    def material_rows(self) -> list[tuple[str, int, int, int, int]]:
        """(素材名, 残り合計, 所持, 不足, 変換流入) の一覧を返す。

        既知の全素材＋所持リストに載っている素材を対象にする。

        レア度変換（緑3→青1, 青3→紫1）を考慮して不足を計算する:
          - 緑: 不足 = max(0, 残り - 所持)。余剰は青へ。
          - 青: 緑の余剰÷3 を「変換流入」として所持に上乗せし、不足を減らす。
                上乗せ後の余剰は紫へ。
          - 紫: 青の余剰（変換流入込み）÷3 を変換流入として上乗せ。
        「変換流入」が ()書きで表示される下位からの変換可能数。
        """
        remaining = self.total_remaining()
        shortage: dict[str, int] = {}
        converted_in: dict[str, int] = {}

        # 緑青紫ファミリーごとに上方変換をカスケード
        for g, b, p in gd.material_families():
            ng, nb, np_ = remaining.get(g, 0), remaining.get(b, 0), remaining.get(p, 0)
            og, ob, op = self.owned(g), self.owned(b), self.owned(p)

            conv_b = max(0, og - ng) // gd.UPGRADE_RATIO       # 緑余剰→青
            eff_b = ob + conv_b
            conv_p = max(0, eff_b - nb) // gd.UPGRADE_RATIO     # 青余剰→紫

            shortage[g] = max(0, ng - og)
            shortage[b] = max(0, nb - eff_b)
            shortage[p] = max(0, np_ - (op + conv_p))
            converted_in[g] = 0
            converted_in[b] = conv_b
            converted_in[p] = conv_p

        names = set(gd.all_materials()) | set(self.inventory) | set(remaining)
        rows = []
        for name in sorted(names, key=gd.sort_key):
            rem = remaining.get(name, 0)
            own = self.owned(name)
            if name in shortage:  # ファミリー素材
                rows.append((name, rem, own, shortage[name], converted_in[name]))
            else:                 # 単一素材（異象狩り/巡礼）・カスタム
                rows.append((name, rem, own, max(0, rem - own), 0))
        return rows

    def to_dict(self) -> dict:
        return {
            "characters": [ch.to_dict() for ch in self.characters],
            "inventory": dict(self.inventory),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Project":
        inv = {str(k): int(v) for k, v in d.get("inventory", {}).items()}
        return cls(
            characters=[Character.from_dict(c) for c in d.get("characters", [])],
            inventory=inv,
        )
