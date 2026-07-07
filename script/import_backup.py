#!/usr/bin/env python3
"""CSVバックアップを新しいSupabaseプロジェクトにインポートする"""

import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from supabase import create_client

BACKUP_DIR = Path(__file__).parent.parent / 'data' / 'backup'

# テーブルの依存関係順にインポート（外部キー制約を考慮）
IMPORT_ORDER = [
    ('cameras_rows.csv',        'cameras'),
    ('housings_rows.csv',       'housings'),
    ('lenses_rows.csv',         'lenses'),
    ('ports_rows.csv',          'ports'),
    ('adapters_rows.csv',       'adapters'),
    ('extensions_rows.csv',     'extensions'),
    ('strobes_rows.csv',        'strobes'),
    ('lights_rows.csv',         'lights'),
    ('accessories_rows.csv',    'accessories'),
    ('gears_rows.csv',          'gears'),
    ('system_charts_rows.csv',  'system_charts'),
    ('creatures_rows.csv',      'creatures'),
    ('diving_points_rows.csv',  'diving_points'),
]

CHUNK_SIZE = 500


def import_table(supabase, table: str, csv_path: Path):
    print(f"  {table} ... ", end='', flush=True)
    with open(csv_path, encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("0件 (スキップ)")
        return

    # 数値変換
    for row in rows:
        for k, v in row.items():
            if v == '':
                row[k] = None

    total = 0
    for i in range(0, len(rows), CHUNK_SIZE):
        chunk = rows[i:i + CHUNK_SIZE]
        supabase.table(table).upsert(chunk).execute()
        total += len(chunk)

    print(f"{total}件")


def main():
    url = os.getenv('NEW_SUPABASE_URL')
    key = os.getenv('NEW_SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("エラー: NEW_SUPABASE_URL と NEW_SUPABASE_SERVICE_ROLE_KEY が .env にありません")
        sys.exit(1)

    supabase = create_client(url, key)
    print(f"インポート先: {url}\n")

    for fname, tname in IMPORT_ORDER:
        csv_path = BACKUP_DIR / fname
        if csv_path.exists():
            import_table(supabase, tname, csv_path)
        else:
            print(f"  {tname} ... ファイルなし (スキップ)")

    print("\n完了")


if __name__ == "__main__":
    main()
