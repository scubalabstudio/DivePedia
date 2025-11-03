#!/usr/bin/env python3
"""
システムチャート関係のテーブルデータを全削除し、IDシーケンスを1からリセットするスクリプト
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client

# .envファイルを読み込み
try:
    from dotenv import load_dotenv
    # プロジェクトルートの.envファイルを読み込み
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    print("警告: python-dotenvがインストールされていません")
    print("pip install python-dotenvを実行してください")

def clear_all_tables_at_once(supabase: Client, tables: list) -> bool:
    """
    全テーブルを一括で削除（外部キー制約を回避）
    """
    try:
        print("  全テーブル一括削除を実行中...")
        
        # 各テーブルの件数確認
        total_records = 0
        for table_name in tables:
            count_result = supabase.table(table_name).select('id', count='exact').execute()
            existing_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
            print(f"    {table_name}: {existing_count}件")
            total_records += existing_count
        
        if total_records == 0:
            print("    全テーブルが既に空です")
            return True
        
        # 外部キー制約を無視して強制削除
        for table_name in tables:
            try:
                # gte('id', 0)で全データを削除
                result = supabase.table(table_name).delete().gte('id', 0).execute()
                print(f"    {table_name} 削除試行完了")
            except Exception as e:
                print(f"    {table_name} 削除エラー（継続）: {e}")
        
        # 削除確認
        remaining_total = 0
        for table_name in tables:
            verify_result = supabase.table(table_name).select('id', count='exact').execute()
            remaining_count = verify_result.count if hasattr(verify_result, 'count') else len(verify_result.data)
            if remaining_count > 0:
                print(f"    {table_name}: まだ{remaining_count}件残っています")
                remaining_total += remaining_count
        
        if remaining_total == 0:
            print("    確認: 全テーブルが完全に空になりました")
            return True
        else:
            print(f"    警告: 合計{remaining_total}件が削除できませんでした")
            return False
        
    except Exception as e:
        print(f"  一括削除エラー: {e}")
        return False

def clear_table_data_with_sql(table_name: str, supabase: Client) -> bool:
    """
    個別テーブル削除（非推奨、一括削除を推奨）
    """
    try:
        print(f"  {table_name}テーブルをクリア中...")
        
        # 既存データ数を確認
        count_result = supabase.table(table_name).select('id', count='exact').execute()
        existing_count = count_result.count if hasattr(count_result, 'count') else len(count_result.data)
        print(f"    削除対象: {existing_count}件")
        
        if existing_count > 0:
            # バッチ削除を試行
            result = supabase.table(table_name).delete().gte('id', 0).execute()
            print(f"    削除完了")
                
            # 削除確認
            verify_result = supabase.table(table_name).select('id', count='exact').execute()
            remaining_count = verify_result.count if hasattr(verify_result, 'count') else len(verify_result.data)
            if remaining_count > 0:
                print(f"    警告: まだ{remaining_count}件残っています")
                return False
            else:
                print(f"    確認: テーブルが完全に空になりました")
        else:
            print(f"    テーブルは既に空です")
        
        print(f"  ✓ {table_name}完了")
        return True
        
    except Exception as e:
        print(f"  ✗ {table_name}エラー: {e}")
        return False

def main():
    # 環境変数からsupabase設定を取得
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("Error: SUPABASE_URL と SUPABASE_SERVICE_ROLE_KEY 環境変数を設定してください")
        sys.exit(1)
    
    print(f"Connecting to Supabase: {url}")
    supabase: Client = create_client(url, key)
    
    # 削除対象テーブル（外部キー制約を考慮して順序指定）
    # system_chartsが他のテーブルを参照しているため、system_chartsを最初に削除してから
    # 参照されているテーブルを削除する
    tables_to_clear = [
        'system_charts',  # 最初に削除（他テーブルを参照）
        'cameras',
        'housings', 
        'lenses',
        'gears',
        'adapters',
        'extensions',
        'ports',
    ]
    
    print("\n=== システムチャート関係テーブルクリア開始 ===")
    
    # 一括削除を試行
    if clear_all_tables_at_once(supabase, tables_to_clear):
        print(f"\n=== クリア完了 ===")
        print("全テーブルのクリアが完了しました。")
        success = True
    else:
        print(f"\n=== 一括削除失敗、個別削除を試行 ===")
        success_count = 0
        total_count = len(tables_to_clear)
        
        for table_name in tables_to_clear:
            if clear_table_data_with_sql(table_name, supabase):
                success_count += 1
        
        print(f"\n=== クリア完了 ===")
        print(f"成功: {success_count}/{total_count}テーブル")
        success = (success_count == total_count)
    
    if success:
        print("\n注意: PostgreSQLのIDシーケンスは自動でリセットされません。")
        print("次回データ挿入時に、IDが以前の続きから開始される可能性があります。")
        print("IDを1から開始したい場合は、Supabaseの管理画面またはSQL Editorで")
        print("以下のコマンドを各テーブルに対して実行してください:")
        print("")
        for table in tables_to_clear:
            print(f"  ALTER SEQUENCE {table}_id_seq RESTART WITH 1;")
    else:
        print("一部のテーブルでエラーが発生しました。")
        sys.exit(1)

if __name__ == "__main__":
    main()