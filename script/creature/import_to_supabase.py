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

def test_connection():
    try:
        get_client().table('creatures').select('*').limit(1).execute()
        return True
    except Exception:
        return False

def import_creatures(json_file_path, mode='append'):
    """生き物データをSupabaseにインポート
    
    Args:
        json_file_path: JSONファイルのパス
        mode: 'append' (追加のみ), 'update' (更新), 'replace' (置換)
    """
    print("📚 JSONファイルを読み込み中...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        creatures = json.load(f)
    print(f"📊 {len(creatures)}件のデータを検出")
    
    # 接続テスト
    if not test_connection():
        print("❌ Supabaseへの接続に失敗しました")
        return 0
    
    # Supabaseクライアント取得
    supabase = get_client()
    
    # 既存データを取得（重複チェック用）
    print("🔍 既存データを確認中...")
    try:
        existing_data = supabase.table('creatures').select('*').execute()
        existing_creatures = existing_data.data if existing_data.data else []
    except Exception as e:
        print(f"⚠️ 既存データ取得エラー: {e}")
        existing_creatures = []
    
    # 既存データのキーを作成（name + categoryで識別）
    existing_keys = set()
    existing_dict = {}
    for creature in existing_creatures:
        # name + categoryで一意性を判定
        key = f"{creature.get('name')}:{creature.get('category', 'unknown')}"
        existing_keys.add(key)
        existing_dict[key] = creature
    
    print(f"📂 既存データ: {len(existing_creatures)}件")
    
    # モードに応じた処理
    if mode == 'replace':
        print("🗑️ 既存データをクリア中...")
        try:
            supabase.table('creatures').delete().neq('id', 0).execute()
            existing_keys.clear()
            existing_dict.clear()
            print("✅ 既存データをクリアしました")
        except Exception as e:
            print(f"⚠️ クリア時のエラー: {e}")
    
    # データ整形と重複チェック
    formatted_creatures = []
    skipped_count = 0
    duplicate_count = 0
    duplicates = []
    
    for creature in creatures:
        # nameがない場合はスキップ
        if not creature.get('name'):
            skipped_count += 1
            print(f"  ⚠️ スキップ: 名前がありません")
            continue
        
        # カテゴリーを判定（データ構造に応じて調整）
        category = creature.get('category', 'unknown')
        if not category:
            # カテゴリーがない場合、他のフィールドから推測
            if 'fish' in str(creature).lower():
                category = 'fish'
            elif 'slug' in str(creature).lower() or 'ウミウシ' in creature.get('name', ''):
                category = 'sea_slug'
            elif 'crab' in str(creature).lower() or 'shrimp' in str(creature).lower() or 'エビ' in creature.get('name', '') or 'カニ' in creature.get('name', ''):
                category = 'crustacean'
            else:
                category = 'other'
        
        # データ整形
        formatted_creature = {
            'name': creature.get('name'),
            'category': category,
            'original_id': creature.get('id') or creature.get('original_id'),
            'description': creature.get('description'),
            'scientific_name': creature.get('scientific_name'),
            'habitat': creature.get('habitat')
        }
        
        # Noneの値を除去
        formatted_creature = {k: v for k, v in formatted_creature.items() if v is not None}
        
        # 重複チェック用のキーを生成
        key = f"{formatted_creature['name']}:{formatted_creature.get('category', 'unknown')}"
        
        # 重複チェック
        if key in existing_keys and mode != 'replace':
            duplicate_count += 1
            duplicates.append(formatted_creature)
            if duplicate_count <= 5:  # 最初の5件だけ表示
                print(f"  ⏭️ 重複スキップ: {formatted_creature['name']} ({formatted_creature.get('category', 'unknown')})")
        else:
            # 新規データ
            formatted_creatures.append(formatted_creature)
    
    print(f"\n📝 インポート対象: {len(formatted_creatures)}件（新規）")
    print(f"⏭️ 重複スキップ: {duplicate_count}件")
    print(f"⚠️ データ不備スキップ: {skipped_count}件\n")
    
    # カテゴリー別の統計
    if formatted_creatures:
        category_stats = {}
        for creature in formatted_creatures:
            cat = creature.get('category', 'unknown')
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        print("📊 カテゴリー別内訳（新規）:")
        for cat, count in sorted(category_stats.items()):
            cat_name = {
                'fish': '魚類',
                'sea_slug': 'ウミウシ',
                'crustacean': 'エビ・カニ',
                'other': 'その他',
                'unknown': '不明'
            }.get(cat, cat)
            print(f"  {cat_name}: {count}件")
    
    # バッチ処理でインポート
    batch_size = 500
    total_imported = 0
    failed_batches = []
    
    if formatted_creatures:
        print("\n🚀 データをインポート中...")
        for i in range(0, len(formatted_creatures), batch_size):
            batch = formatted_creatures[i:i + batch_size]
            try:
                result = supabase.table('creatures').insert(batch).execute()
                total_imported += len(batch)
                print(f"✅ {total_imported}/{len(formatted_creatures)} 件インポート完了")
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
    print(f"✅ 新規追加: {total_imported}件")
    print(f"⏭️ 重複スキップ: {duplicate_count}件")
    print(f"❌ 失敗: {len(formatted_creatures) - total_imported}件")
    print(f"⚠️ データ不備: {skipped_count}件")
    
    if failed_batches:
        print("\n❌ 失敗したバッチ:")
        for batch in failed_batches[:5]:  # 最初の5件だけ表示
            print(f"  - {batch['range']}: {batch['error']}")
    
    return total_imported

def verify_import():
    """インポート結果を確認"""
    supabase = get_client()
    
    try:
        # 全件数を確認
        result = supabase.table('creatures').select('*', count='exact').execute()
        print(f"\n✅ 総登録数: {result.count}件")
        
        # カテゴリー別に確認
        print("\n📊 カテゴリー別件数:")
        for category in ['fish', 'sea_slug', 'crustacean', 'other', 'unknown']:
            result = supabase.table('creatures').select('*', count='exact').eq('category', category).execute()
            if result.count > 0:
                category_name = {
                    'fish': '魚類',
                    'sea_slug': 'ウミウシ',
                    'crustacean': 'エビ・カニ',
                    'other': 'その他',
                    'unknown': '不明'
                }.get(category, category)
                print(f"  {category_name}: {result.count}件")
        
        # サンプルデータを表示
        sample_result = supabase.table('creatures').select('name, category').limit(5).execute()
        if sample_result.data:
            print("\n📋 サンプルデータ（最初の5件）:")
            for creature in sample_result.data:
                cat_name = {
                    'fish': '魚類',
                    'sea_slug': 'ウミウシ',
                    'crustacean': 'エビ・カニ',
                    'other': 'その他',
                    'unknown': '不明'
                }.get(creature.get('category', 'unknown'), creature.get('category', 'unknown'))
                print(f"  - {creature['name']} ({cat_name})")
                
    except Exception as e:
        print(f"❌ 確認時のエラー: {e}")

def check_duplicates(json_file_path):
    """重複チェックのみ実行"""
    print("🔍 重複チェックモード\n")
    
    # JSONファイルを読み込み
    with open(json_file_path, 'r', encoding='utf-8') as f:
        creatures = json.load(f)
    
    print(f"📊 チェック対象: {len(creatures)}件")
    
    # Supabaseクライアント取得
    supabase = get_client()
    
    # 既存データを取得
    try:
        existing_data = supabase.table('creatures').select('*').execute()
        existing_creatures = existing_data.data if existing_data.data else []
    except Exception as e:
        print(f"❌ 既存データ取得エラー: {e}")
        return
    
    print(f"📂 既存データ: {len(existing_creatures)}件")
    
    # 既存データのキーを作成
    existing_keys = {}
    for creature in existing_creatures:
        key = f"{creature.get('name')}:{creature.get('category', 'unknown')}"
        existing_keys[key] = creature
    
    # 重複チェック
    duplicates = []
    new_creatures = []
    
    for creature in creatures:
        if not creature.get('name'):
            continue
        
        category = creature.get('category', 'unknown')
        key = f"{creature.get('name')}:{category}"
        
        if key in existing_keys:
            duplicates.append(creature)
        else:
            new_creatures.append(creature)
    
    print(f"\n📊 チェック結果:")
    print(f"  ✨ 新規追加可能: {len(new_creatures)}件")
    print(f"  ⏭️ 重複: {len(duplicates)}件")
    
    if duplicates and len(duplicates) <= 10:
        print("\n📋 重複データ詳細（最初の10件）:")
        for dup in duplicates[:10]:
            print(f"  - {dup.get('name')} ({dup.get('category', 'unknown')})")

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: python import_to_supabase.py <JSONファイルパス> [オプション]")
        print("\nオプション:")
        print("  --check   : 重複チェックのみ")
        print("  --replace : 既存データを削除して置換")
        print("  --update  : 既存データは更新、新規は追加")
        print("\n例:")
        print("  python import_to_supabase.py data/creatures.json")
        print("  python import_to_supabase.py data/creatures.json --check")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # ファイル存在確認
    if not os.path.exists(json_file):
        print(f"❌ ファイルが見つかりません: {json_file}")
        sys.exit(1)
    
    # オプション処理
    mode = 'append'
    if len(sys.argv) > 2:
        if sys.argv[2] == '--check':
            check_duplicates(json_file)
            return
        elif sys.argv[2] == '--replace':
            mode = 'replace'
        elif sys.argv[2] == '--update':
            mode = 'update'
    
    # インポート実行
    print(f"📝 モード: {mode}")
    imported = import_creatures(json_file, mode)
    
    # 結果確認
    if imported > 0 or mode == 'replace':
        verify_import()

if __name__ == "__main__":
    main()