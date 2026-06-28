"""Project の JSON 保存・読み込み。

保存先は既定で ユーザーフォルダ配下 (~/.nte_material/data.json)。
壊れたファイルや不在時は空の Project を返す。
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Project

DEFAULT_PATH = Path.home() / ".nte_material" / "data.json"


def load(path: Path = DEFAULT_PATH) -> Project:
    """JSON から Project を読み込む。無ければ空の Project。"""
    if not path.exists():
        return Project()
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        return Project.from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        # 壊れている場合は空で開始（既存ファイルは上書きしない判断は呼び出し側）
        return Project()


def save(project: Project, path: Path = DEFAULT_PATH) -> None:
    """Project を JSON へ保存する（親フォルダは自動作成）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)
    tmp.replace(path)  # 原子的に差し替え（保存中クラッシュで壊れにくい）
