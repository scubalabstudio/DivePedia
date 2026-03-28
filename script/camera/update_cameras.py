#!/usr/bin/env python3
"""
cameras_rows.csv を使って Supabase の cameras テーブルを更新するスクリプト

【機能】
- data/backup_data/cameras_rows.csv の内容で Supabase の cameras テーブルを upsert
- id を基準に既存レコードを更新、存在しない場合は新規挿入

【使用方法】
python3 script/camera/update_cameras.py

【前提条件】
- .env ファイルに以下の環境変数を設定
  SUPABASE_URL=your_supabase_url
  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
- 必要なパッケージをインストール
  pip install supabase python-dotenv
"""

import csv
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    print("警告: python-dotenv がインストールされていません")

try:
    from supabase import create_client, Client
except ImportError:
    print("エラー: supabase パッケージがインストールされていません")
    print("pip install supabase を実行してください")
    sys.exit(1)

CSV_PATH = Path(__file__).parent.parent.parent / 'data' / 'backup' / 'cameras_rows.csv'


def load_csv() -> list[dict]:
    rows = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                'id': int(row['id']),
                'model': row['model'],
                'display_name': row['display_name'],
                'brand': row['brand'],
                'created_at': row['created_at'],
                'type': row['type'],
            })
    return rows


def update_cameras(supabase: Client, rows: list[dict]):
    print(f"対象レコード数: {len(rows)}")

    # Supabase の現在のデータを取得して差分確認
    existing = supabase.table('cameras').select('id, model, display_name, brand, type').execute()
    existing_map = {row['id']: row for row in existing.data}

    updated = []
    skipped = []

    for row in rows:
        rid = row['id']
        current = existing_map.get(rid)

        if current is None:
            # 新規レコード
            updated.append(row)
            print(f"  [NEW] id={rid}: {row['model']}")
            continue

        # 差分チェック
        changed = (
            current['model'] != row['model'] or
            current['display_name'] != row['display_name'] or
            current['brand'] != row['brand'] or
            current['type'] != row['type']
        )

        if changed:
            updated.append(row)
            print(f"  [UPDATE] id={rid}: model={current['model']!r} → {row['model']!r}")
        else:
            skipped.append(rid)

    print(f"\n変更あり: {len(updated)}件 / スキップ: {len(skipped)}件")

    if not updated:
        print("更新するデータがありません")
        return

    # upsert で一括更新
    result = supabase.table('cameras').upsert(updated).execute()
    print(f"upsert 完了: {len(result.data)}件")


def main():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("エラー: SUPABASE_URL と SUPABASE_SERVICE_ROLE_KEY を .env に設定してください")
        sys.exit(1)

    if not CSV_PATH.exists():
        print(f"エラー: CSV ファイルが見つかりません: {CSV_PATH}")
        sys.exit(1)

    print(f"Supabase に接続中: {url}")
    supabase: Client = create_client(url, key)

    rows = load_csv()
    update_cameras(supabase, rows)


if __name__ == "__main__":
    main()
