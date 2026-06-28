"""素材アイコンの読み込み。

方針（再配布を考慮した差し替え可能構成）:
  1. assets/icons/<安全化した素材名>.png があればそれを表示。
  2. 無ければレア度色（緑/青/紫）のプレースホルダを動的生成（追加依存なし）。

実画像ファイルは別資産として扱い、差し替え・削除が自由。再配布する場合は
assets/icons を空にすれば、コードはプレースホルダにフォールバックする。
（assets/icons/*.png は .gitignore 済み＝リポジトリは画像を同梱しない）
"""

from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path

from . import gamedata as gd

# プロジェクトルート/assets/icons
ICON_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"
ICON_SIZE = 24  # 表示目安（px）

_RARITY_COLOR = {gd.G: "#3aa655", gd.B: "#3b82c4", gd.P: "#9b59b6"}
_DEFAULT_COLOR = "#8a8a8a"
_BORDER_COLOR = "#2b2b2b"


def safe_filename(material: str) -> str:
    """素材名をファイル名に使える形へ（禁則文字を _ に置換）。"""
    return re.sub(r'[\\/:*?"<>|]', "_", material)


def _rarity_map() -> dict[str, str]:
    """素材名 -> レア度（緑/青/紫）。単一素材（異象狩り/巡礼）は対象外。"""
    out: dict[str, str] = {}
    for src in (gd.IKUSEI_LINES, gd.CARD_ROWS, gd.ARC_SPECIAL_ROWS):
        for row in src.values():
            for rarity, name in row.items():
                out[name] = rarity
    return out


class IconManager:
    """PhotoImage を生成・キャッシュする。GC されないよう参照を保持する。"""

    def __init__(self) -> None:
        self._cache: dict[str, tk.PhotoImage] = {}
        self._rarity = _rarity_map()

    def get(self, material: str) -> tk.PhotoImage:
        img = self._cache.get(material)
        if img is None:
            img = self._load_file(material) or self._placeholder(material)
            self._cache[material] = img
        return img

    def _load_file(self, material: str) -> tk.PhotoImage | None:
        path = ICON_DIR / f"{safe_filename(material)}.png"
        if not path.exists():
            return None
        try:
            img = tk.PhotoImage(file=str(path))
        except tk.TclError:
            return None  # PNG以外などは無視してプレースホルダへ
        # 大きい画像は整数倍で縮小（subsample は整数のみ・四捨五入で近づける）
        factor = max(1, round(max(img.width(), img.height()) / ICON_SIZE))
        return img.subsample(factor, factor) if factor > 1 else img

    def _placeholder(self, material: str) -> tk.PhotoImage:
        color = _RARITY_COLOR.get(self._rarity.get(material, ""), _DEFAULT_COLOR)
        img = tk.PhotoImage(width=ICON_SIZE, height=ICON_SIZE)
        img.put(_BORDER_COLOR, to=(0, 0, ICON_SIZE, ICON_SIZE))
        img.put(color, to=(2, 2, ICON_SIZE - 2, ICON_SIZE - 2))
        return img
