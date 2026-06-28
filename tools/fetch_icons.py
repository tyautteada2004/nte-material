"""assets/icon_sources.json の URL からアイコンを assets/icons/ へ取得・変換する。

    python tools/fetch_icons.py

icon_sources.json は「素材名 -> 画像URL」の対応表。URL が空の項目はスキップ。
保存名は素材名を安全化した <名前>.png（アプリが参照するファイル名と一致）。

Tkinter は PNG / GIF しか表示できないため、webp など PNG 以外は **Pillow** で
PNG へ変換して保存する。Pillow が未インストールの場合、PNG 以外はスキップする
（`pip install pillow` 後に再実行）。アプリ本体は標準ライブラリのみで動作し、
本スクリプト（セットアップ用）だけが任意で Pillow を使う。

【権利の注意】
ここで取得する画像はゲーム運営（NetEase / Hotta Studio 等）の著作物である
可能性があります。個人利用に留めてください。assets/icons/*.png は .gitignore
されており、リポジトリには同梱されません。再配布する場合は assets/icons を
空にする（アプリは自動でプレースホルダ表示にフォールバック）か、権利的に
問題ない画像へ差し替えてください。
"""

from __future__ import annotations

import io
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nte_material.icons import ICON_DIR, safe_filename  # noqa: E402

MANIFEST = Path(__file__).resolve().parents[1] / "assets" / "icon_sources.json"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

try:
    from PIL import Image  # type: ignore

    _HAS_PIL = True
except ImportError:  # Pillow が無くても PNG ソースなら動く
    _HAS_PIL = False


def _save_as_png(data: bytes, dest: Path) -> str:
    """画像バイト列を PNG として保存する。返り値は状態文字列。"""
    if data[:8] == _PNG_MAGIC:
        dest.write_bytes(data)
        return "png"
    if not _HAS_PIL:
        return "need_pillow"
    with Image.open(io.BytesIO(data)) as im:
        im.convert("RGBA").save(dest, format="PNG")
    return "converted"


def main() -> int:
    if not MANIFEST.exists():
        print(f"manifest が見つかりません: {MANIFEST}")
        return 1
    sources: dict[str, str] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    ok = skip = fail = need_pillow = 0
    for material, url in sources.items():
        if not url:
            skip += 1
            continue
        dest = ICON_DIR / f"{safe_filename(material)}.png"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            status = _save_as_png(data, dest)
            if status == "need_pillow":
                need_pillow += 1
                print(f"SKIP {material}: PNG以外（Pillow未導入で変換不可）")
            else:
                ok += 1
                print(f"OK   {material}" + (" (webp→png変換)" if status == "converted" else ""))
        except Exception as e:  # noqa: BLE001 - ネットワーク系を一括で握る
            fail += 1
            print(f"FAIL {material}: {e}")

    print(f"\n取得 {ok} / 失敗 {fail} / 未設定 {skip} / 要Pillow {need_pillow}")
    if need_pillow:
        print("PNG以外の変換には Pillow が必要です: pip install pillow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
