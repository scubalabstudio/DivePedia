import json
import sys
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent.parent.parent / '.env')

def get_client():
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )

def import_diving_points(json_file_path):
    """ダイビングポイントデータをSupabaseにインポート"""
    
    print("📚 JSONファイルを読み込み中...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        points = json.load(f)
    
    print(f"📊 {len(points)}件のデータを検出")
    
    # Supabaseクライアント取得
    supabase = get_client()
    
    # 既存データをクリア（オプション）
    print("🗑️ 既存データをクリア中...")
    try:
        supabase.table('diving_points').delete().neq('id', 0).execute()
    except:
        pass  # テーブルが空の場合はエラーになるので無視
    
    # データ整形（prefectureがNoneのものは除外）
    formatted_points = []
    skipped_count = 0
    
    for point in points:
        if point.get('prefecture'):  # prefectureがある場合のみ
            formatted_point = {
                'name': point.get('name'),
                'code': point.get('code'),
                'url': point.get('url'),
                'prefecture': point.get('prefecture'),
                'latitude': point.get('latitude'),
                'longitude': point.get('longitude'),
            }
            formatted_points.append(formatted_point)
        else:
            skipped_count += 1
            print(f"  ⚠️ スキップ: {point.get('name')} (都道府県情報なし)")
    
    print(f"\n📝 インポート対象: {len(formatted_points)}件")
    print(f"⏭️ スキップ: {skipped_count}件\n")
    
    # バッチ処理でインポート
    batch_size = 50
    total_imported = 0
    failed_batches = []
    
    for i in range(0, len(formatted_points), batch_size):
        batch = formatted_points[i:i + batch_size]
        try:
            result = supabase.table('diving_points').insert(batch).execute()
            total_imported += len(batch)
            print(f"✅ {total_imported}/{len(formatted_points)} 件インポート完了")
        except Exception as e:
            print(f"❌ エラー: {e}")
            failed_batches.append({
                'range': f"{i}〜{i + len(batch)}",
                'error': str(e),
                'data': batch
            })
    
    # 結果サマリー
    print("\n" + "="*50)
    print("📊 インポート結果サマリー")
    print("="*50)
    print(f"✅ 成功: {total_imported}件")
    print(f"❌ 失敗: {len(formatted_points) - total_imported}件")
    print(f"⏭️ スキップ: {skipped_count}件")
    
    if failed_batches:
        print("\n❌ 失敗したバッチ:")
        for batch in failed_batches:
            print(f"  - {batch['range']}: {batch['error']}")
    
    # 都道府県別の集計
    print("\n📍 都道府県別インポート数:")
    prefecture_count = {}
    for point in formatted_points[:total_imported]:
        pref = point['prefecture']
        prefecture_count[pref] = prefecture_count.get(pref, 0) + 1
    
    for pref, count in sorted(prefecture_count.items()):
        print(f"  {pref}: {count}件")
    
    return total_imported

def verify_import():
    """インポート結果を確認"""
    supabase = get_client()
    
    # 全件数を確認
    result = supabase.table('diving_points').select('*', count='exact').execute()
    print(f"\n✅ 総登録数: {result.count}件")
    
    # 都道府県別に確認
    all_points = supabase.table('diving_points').select('prefecture').execute()
    prefecture_count = {}
    for point in all_points.data:
        pref = point['prefecture']
        prefecture_count[pref] = prefecture_count.get(pref, 0) + 1
    
    print("\n都道府県別:")
    for pref, count in sorted(prefecture_count.items()):
        print(f"  {pref}: {count}件")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        
        # ファイル存在確認
        if not os.path.exists(json_file):
            print(f"❌ ファイルが見つかりません: {json_file}")
            sys.exit(1)
        
        # インポート実行
        imported = import_diving_points(json_file)
        
        # 結果確認
        if imported > 0:
            verify_import()
    else:
        print("使用方法: python import.py <JSONファイルパス>")
        print("例: python import.py ../../data/processed/diving_points_with_prefecture.json")
