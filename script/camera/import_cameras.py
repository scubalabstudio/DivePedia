#!/usr/bin/env python3
"""
data/processed/camera/cameras.json を Supabase の cameras テーブルにインポートするスクリプト

【機能】
- Supabase に存在しないカメラのみ新規挿入（model で重複チェック）
- 既存カメラはスキップ

【使用方法】
python3 script/camera/import_cameras.py

【新しいカメラを追加する手順】
1. data/processed/camera/cameras.json にエントリを追加
2. このスクリプトを実行
3. script/export_backup.py cameras で backup を更新
"""

import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
except ImportError:
    pass

try:
    from supabase import create_client
except ImportError:
    print('エラー: pip install supabase')
    sys.exit(1)

INPUT_FILE = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'camera' / 'cameras.json'

VALID_TYPES = {'dslr', 'mirrorless', 'compact'}


def validate(camera: dict):
    """バリデーション。エラーメッセージを返す（問題なければ None）"""
    for field in ('model', 'display_name', 'brand', 'type'):
        if not camera.get(field):
            return f"必須フィールドが空: {field}"
    if camera['type'] not in VALID_TYPES:
        return f"type が不正: {camera['type']} (dslr / mirrorless / compact)"
    return None


def main():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    if not url or not key:
        print('エラー: SUPABASE_URL と SUPABASE_SERVICE_ROLE_KEY を .env に設定してください')
        sys.exit(1)

    if not INPUT_FILE.exists():
        print(f'エラー: {INPUT_FILE} が見つかりません')
        print('先に generate_processed.py を実行してください')
        sys.exit(1)

    with open(INPUT_FILE, encoding='utf-8') as f:
        cameras = json.load(f)

    supabase = create_client(url, key)

    # 既存の model 一覧を取得
    existing = supabase.table('cameras').select('model').execute()
    existing_models = {row['model'] for row in existing.data}

    new_cameras = []
    skipped = []
    errors = []

    for cam in cameras:
        err = validate(cam)
        if err:
            errors.append(f"  スキップ (バリデーションエラー): {cam} → {err}")
            continue
        if cam['model'] in existing_models:
            skipped.append(cam['model'])
        else:
            new_cameras.append({
                'model':        cam['model'],
                'display_name': cam['display_name'],
                'brand':        cam['brand'],
                'type':         cam['type'],
            })

    print(f"既存: {len(skipped)}件 / 新規: {len(new_cameras)}件 / エラー: {len(errors)}件")

    if errors:
        for e in errors:
            print(e)

    if not new_cameras:
        print('追加するカメラがありません')
        return

    result = supabase.table('cameras').insert(new_cameras).execute()
    for row in result.data:
        print(f"  [追加] id={row['id']}, model={row['model']!r}")

    print(f'\n完了: {len(result.data)}件追加')
    print('次に script/export_backup.py cameras を実行して backup を更新してください')


if __name__ == '__main__':
    main()
