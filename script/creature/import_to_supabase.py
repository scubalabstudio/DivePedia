# import_to_supabase.py

import json
import os
from supabase import create_client, Client
from typing import List, Dict

# Supabaseの設定
SUPABASE_URL = "https://ihyksziopqzyalrznfqr.supabase.co"
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

if not SUPABASE_KEY:
    print("エラー: SUPABASE_SERVICE_KEY環境変数が設定されていません")
    print("実行方法: export SUPABASE_SERVICE_KEY='your-service-role-key-here'")
    exit(1)

def load_json_data(file_path: str) -> List[Dict]:
    """JSONファイルからデータを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ {file_path} を読み込みました: {len(data)}件")
        return data
    except FileNotFoundError:
        print(f"⚠️ {file_path} が見つかりません")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ {file_path} のJSON解析エラー: {e}")
        return []

def prepare_creatures_data():
    """データを統一フォーマットに変換"""
    creatures = []
    
    # 魚類データ
    fish_data = load_json_data('fish_data.json')
    for item in fish_data:
        creatures.append({
            'name': item['name'],
            'category': 'fish',
            'original_id': item.get('id', None)
        })
    
    # ウミウシデータ
    sea_slug_data = load_json_data('sea_slug_data.json')
    for item in sea_slug_data:
        creatures.append({
            'name': item['name'],
            'category': 'sea_slug',
            'original_id': item.get('id', None)
        })
    
    # エビ・カニ・その他データ
    crustacean_data = load_json_data('crustacean_other_data.json')
    for item in crustacean_data:
        creatures.append({
            'name': item['name'],
            'category': 'crustacean',
            'original_id': item.get('id', None)
        })
    
    return creatures

def import_to_supabase():
    """Supabaseにデータをインポート"""
    
    print("\n🚀 Supabaseへのインポートを開始します...")
    
    # Supabaseクライアントを作成
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabaseに接続しました")
    except Exception as e:
        print(f"❌ Supabase接続エラー: {e}")
        return
    
    # データを準備
    creatures = prepare_creatures_data()
    
    if not creatures:
        print("❌ インポートするデータがありません")
        return
    
    print(f"\n📊 データ統計:")
    print(f"  合計: {len(creatures)}件")
    
    # カテゴリー別の件数を表示
    categories = {}
    for creature in creatures:
        cat = creature['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, count in categories.items():
        cat_name = {
            'fish': '魚類',
            'sea_slug': 'ウミウシ',
            'crustacean': 'エビ・カニ・その他'
        }.get(cat, cat)
        print(f"  {cat_name}: {count}件")
    
    # 既存データをクリア
    try:
        print("\n🗑️ 既存データをクリア中...")
        result = supabase.table('creatures').delete().neq('id', 0).execute()
        print("✅ 既存データをクリアしました")
    except Exception as e:
        print(f"⚠️ クリア時の警告（続行します）: {e}")
    
    # バッチサイズを設定（一度に挿入するレコード数）
    batch_size = 500
    success_count = 0
    error_count = 0
    
    # データをバッチで挿入
    print("\n📥 データをインポート中...")
    for i in range(0, len(creatures), batch_size):
        batch = creatures[i:i + batch_size]
        batch_end = min(i + batch_size, len(creatures))
        
        try:
            result = supabase.table('creatures').insert(batch).execute()
            success_count += len(batch)
            print(f"  ✅ {i + 1} - {batch_end} / {len(creatures)} 完了")
        except Exception as e:
            error_count += len(batch)
            print(f"  ❌ {i + 1} - {batch_end} / {len(creatures)} エラー: {e}")
            # エラーが発生しても続行
            continue
    
    # インポート結果を確認
    print("\n📊 インポート結果:")
    print(f"  成功: {success_count}件")
    print(f"  失敗: {error_count}件")
    
    try:
        # 総件数を確認
        count_result = supabase.table('creatures').select('*', count='exact').execute()
        print(f"\n✅ データベース内の総レコード数: {count_result.count}件")
        
        # カテゴリー別の件数を確認
        print("\n📊 カテゴリー別件数（DB内）:")
        for category in ['fish', 'sea_slug', 'crustacean']:
            result = supabase.table('creatures').select('*', count='exact').eq('category', category).execute()
            category_name = {
                'fish': '魚類',
                'sea_slug': 'ウミウシ',
                'crustacean': 'エビ・カニ・その他'
            }[category]
            print(f"  {category_name}: {result.count}件")
    except Exception as e:
        print(f"⚠️ 件数確認時のエラー: {e}")
    
    print("\n✨ インポート処理が完了しました！")

if __name__ == "__main__":
    # ファイルの存在確認
    print("📁 ファイルチェック:")
    files = ['fish_data.json', 'sea_slug_data.json', 'crustacean_other_data.json']
    all_exist = True
    
    for file in files:
        if os.path.exists(file):
            print(f"  ✅ {file} が存在します")
        else:
            print(f"  ❌ {file} が見つかりません")
            all_exist = False
    
    if not all_exist:
        print("\n⚠️ 必要なファイルが揃っていません")
        print("以下のファイルが必要です:")
        for file in files:
            print(f"  - {file}")
        exit(1)
    
    # インポート実行
    import_to_supabase()
