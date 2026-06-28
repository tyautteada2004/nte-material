"""assets/icon_sources.json の URL からアイコンを assets/icons/ へダウンロードする。

    python tools/fetch_icons.py

icon_sources.json は「素材名 -> 画像URL」の対応表。URL が空の項目はスキップ。
保存名は素材名を安全化した <名前>.png（アプリが参照するファイル名と一致）。

【権利の注意】
ここで取得する画像はゲーム運営（NetEase / Hotta Studio 等）の著作物である
可能性があります。個人利用に留めてください。assets/icons/*.png は .gitignore
されており、リポジトリには同梱されません。再配布する場合は assets/icons を
空にする（アプリは自動でプレースホルダ表示にフォールバック）か、権利的に
問題ない画像へ差し替えてください。
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nte_material.icons import ICON_DIR, safe_filename  # noqa: E402

MANIFEST = Path(__file__).resolve().parents[1] / "assets" / "icon_sources.json"


def main() -> int:
    if not MANIFEST.exists():
        print(f"manifest が見つかりません: {MANIFEST}")
        return 1
    sources: dict[str, str] = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    ok = skip = fail = 0
    for material, url in sources.items():
        if not url:
            skip += 1
            continue
        dest = ICON_DIR / f"{safe_filename(material)}.png"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                dest.write_bytes(resp.read())
            ok += 1
            print(f"OK   {material}")
        except Exception as e:  # noqa: BLE001 - ネットワーク系を一括で握る
            fail += 1
            print(f"FAIL {material}: {e}")

    print(f"\n取得 {ok} / 失敗 {fail} / 未設定 {skip}（PNG形式のみアプリで表示可）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
