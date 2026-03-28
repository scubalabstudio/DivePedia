#!/usr/bin/env python3
"""
Supabase の全テーブルを data/backup_data/ に CSV としてエクスポートするスクリプト

【使用方法】
python3 script/export_backup.py

【オプション】
python3 script/export_backup.py cameras          # 特定テーブルのみ
python3 script/export_backup.py cameras housings  # 複数テーブル指定

【前提条件】
- .env ファイルに以下の環境変数を設定
  SUPABASE_URL=your_supabase_url
  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
- pip install supabase python-dotenv
"""

import csv
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    print("警告: python-dotenv がインストールされていません")

try:
    from supabase import create_client, Client
except ImportError:
    print("エラー: supabase パッケージがインストールされていません")
    print("pip install supabase を実行してください")
    sys.exit(1)

BACKUP_DIR = Path(__file__).parent.parent / 'data' / 'backup'

# エクスポート対象テーブル（ファイル名: テーブル名）
TABLES = {
    'accessories_rows.csv':   'accessories',
    'adapters_rows.csv':      'adapters',
    'cameras_rows.csv':       'cameras',
    'creatures_rows.csv':     'creatures',
    'diving_points_rows.csv': 'diving_points',
    'extensions_rows.csv':    'extensions',
    'gears_rows.csv':         'gears',
    'housings_rows.csv':      'housings',
    'lenses_rows.csv':        'lenses',
    'lights_rows.csv':        'lights',
    'ports_rows.csv':         'ports',
    'strobes_rows.csv':       'strobes',
    'system_charts_rows.csv': 'system_charts',
}

PAGE_SIZE = 1000


def fetch_all(supabase: Client, table: str) -> list[dict]:
    """ページネーションで全件取得"""
    rows = []
    offset = 0
    while True:
        result = (
            supabase.table(table)
            .select('*')
            .order('id')
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        batch = result.data
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def export_table(supabase: Client, table: str, csv_path: Path):
    print(f"  {table} ... ", end='', flush=True)
    rows = fetch_all(supabase, table)

    if not rows:
        print("0件 (スキップ)")
        return

    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)}件 → {csv_path.name}")


def main():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("エラー: SUPABASE_URL と SUPABASE_SERVICE_ROLE_KEY を .env に設定してください")
        sys.exit(1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    supabase: Client = create_client(url, key)
    print(f"接続先: {url}\n")

    # コマンドライン引数でテーブルを絞り込み
    target_tables = sys.argv[1:] if len(sys.argv) > 1 else []

    targets = {
        fname: tname
        for fname, tname in TABLES.items()
        if not target_tables or tname in target_tables
    }

    if not targets:
        print(f"エラー: 指定したテーブルが見つかりません: {target_tables}")
        print(f"利用可能: {list(TABLES.values())}")
        sys.exit(1)

    print(f"エクスポート開始: {len(targets)} テーブル")
    for fname, tname in targets.items():
        export_table(supabase, tname, BACKUP_DIR / fname)

    print("\n完了")


if __name__ == "__main__":
    main()
