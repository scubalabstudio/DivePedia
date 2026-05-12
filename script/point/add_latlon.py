import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

INPUT_PATH = Path(__file__).parent.parent.parent / "data/processed/point/diving_spots.json"
OUTPUT_PATH = INPUT_PATH

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "diving-api-geocoder/1.0 (naishutiantou@gmail.com)"}
DELAY_SEC = 1.1  # Nominatim rate limit: 1 req/sec

JP_PREFECTURES = {
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
}


def _clean_name(name: str) -> str:
    """括弧・中点などを除去してシンプルな地名を返す"""
    import re
    # 全角括弧内を除去: 八重干瀬（池間島）→ 八重干瀬
    name = re.sub(r'[（(][^）)]*[）)]', '', name).strip()
    # 中点区切りの先頭部分のみ使用: 黄金崎・安良里 → 黄金崎
    name = name.split('・')[0].strip()
    return name


def _is_japan_coords(lat: float, lon: float) -> bool:
    return 24 <= lat <= 46 and 123 <= lon <= 146


def geocode(name: str, prefecture: str) -> tuple[float | None, float | None]:
    is_japan = prefecture in JP_PREFECTURES
    short_name = _clean_name(name)

    if is_japan:
        queries = [
            (f"{name} {prefecture}", {"countrycodes": "jp"}),
            (f"{short_name} {prefecture}", {"countrycodes": "jp"}),
            (f"{short_name} Japan", {"countrycodes": "jp"}),
        ]
    else:
        queries = [
            (f"{name} {prefecture}", {}),
            (f"{short_name} {prefecture}", {}),
            (f"{short_name}", {}),
        ]

    for query, extra_params in queries:
        params = urllib.parse.urlencode({
            "q": query,
            "format": "json",
            "limit": 1,
            **extra_params,
        })
        req = urllib.request.Request(f"{NOMINATIM_URL}?{params}", headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                results = json.loads(resp.read().decode())
            if results:
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                # 海外スポットに日本の座標が返った場合は無効とみなす
                if not is_japan and _is_japan_coords(lat, lon):
                    time.sleep(DELAY_SEC)
                    continue
                return lat, lon
        except Exception as e:
            print(f"  ⚠️  リクエストエラー ({query}): {e}")
        time.sleep(DELAY_SEC)
    return None, None


def main() -> None:
    with open(INPUT_PATH, encoding="utf-8") as f:
        spots: list[dict] = json.load(f)

    total = len(spots)
    already_done = sum(1 for s in spots if "latitude" in s and s["latitude"] is not None)
    print(f"全 {total} 件 / 既取得済み {already_done} 件")

    updated = 0
    for i, spot in enumerate(spots):
        if "latitude" in spot and spot["latitude"] is not None:
            continue  # 取得済みはスキップ

        name = spot.get("name", "")
        prefecture = spot.get("prefecture", "")
        print(f"[{i + 1}/{total}] {prefecture} {name} を検索中...")

        lat, lon = geocode(name, prefecture)
        spot["latitude"] = lat
        spot["longitude"] = lon

        if lat is not None:
            print(f"  -> {lat}, {lon}")
            updated += 1
        else:
            print(f"  -> 見つかりませんでした")

        # 10件ごとに中間保存
        if (i + 1) % 10 == 0:
            with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(spots, f, ensure_ascii=False, indent=2)
            print(f"  💾 {i + 1} 件まで保存済み")

        time.sleep(DELAY_SEC)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)

    not_found = sum(1 for s in spots if s.get("latitude") is None)
    print(f"\n完了: 新規取得 {updated} 件 / 未取得 {not_found} 件")


if __name__ == "__main__":
    main()
