#!/usr/bin/env python3
"""
E-M5MarkIII の重複レコードを Supabase 上で修正するスクリプト

【修正内容】
1. system_charts の camera_id=138 を camera_id=105 に更新（93件）
2. cameras id=138 を削除
3. cameras id=105 の brand を 'Olympus' に更新

【使用方法】
python3 script/camera/fix_em5markiii_duplicate.py
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
except ImportError:
    pass

try:
    from supabase import create_client, Client
except ImportError:
    print("エラー: pip install supabase")
    sys.exit(1)


def main():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("エラー: SUPABASE_URL と SUPABASE_SERVICE_ROLE_KEY を設定してください")
        sys.exit(1)

    supabase: Client = create_client(url, key)

    # Step 1: system_charts の camera_id=138 → 105 に更新
    print("Step 1: system_charts の camera_id=138 → 105 に更新中...")
    result = (
        supabase.table('system_charts')
        .update({'camera_id': 105})
        .eq('camera_id', 138)
        .execute()
    )
    print(f"  更新: {len(result.data)}件")

    # Step 2: cameras id=138 を削除
    print("Step 2: cameras id=138 を削除中...")
    result = supabase.table('cameras').delete().eq('id', 138).execute()
    print(f"  削除: {len(result.data)}件")

    # Step 3: cameras id=105 の brand を Olympus に更新
    print("Step 3: cameras id=105 の brand を 'Olympus' に更新中...")
    result = (
        supabase.table('cameras')
        .update({'brand': 'Olympus'})
        .eq('id', 105)
        .execute()
    )
    print(f"  更新: {len(result.data)}件")

    print("\n完了")


if __name__ == "__main__":
    main()
