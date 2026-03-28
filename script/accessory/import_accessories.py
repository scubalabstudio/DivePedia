import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Set, Tuple

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).parent.parent.parent / '.env')

def get_client():
    return create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )

def get_existing_accessories(supabase) -> Tuple[Set[str], Dict[str, Dict]]:
    """既存のアクセサリーデータを取得
    
    Returns:
        existing_keys: 重複チェック用のキーのセット
        existing_dict: キーから既存データへのマッピング
    """
    print("🔍 既存データを確認中...")
    existing_keys = set()
    existing_dict = {}
    
    try:
        # 全データを取得（ページネーション対応）
        offset = 0
        limit = 1000
        all_data = []
        
        while True:
            result = supabase.table('accessories').select('*').range(offset, offset + limit - 1).execute()
            if not result.data:
                break
            all_data.extend(result.data)
            if len(result.data) < limit:
                break
            offset += limit
        
        # キーを作成（name + companyで一意性を判定）
        for accessory in all_data:
            # nameとcompanyの組み合わせで一意性を判定
            name = accessory.get('name', '')
            company = accessory.get('company', 'unknown')
            key = f"{name}:{company}"
            existing_keys.add(key)
            existing_dict[key] = accessory
        
        print(f"📂 既存データ: {len(all_data)}件")
        
        # メーカー別の内訳
        company_counts = {}
        for accessory in all_data:
            company = accessory.get('company', '不明')
            company_counts[company] = company_counts.get(company, 0) + 1
        
        if company_counts:
            print("  メーカー別内訳:")
            for company, count in sorted(company_counts.items())[:5]:  # 上位5社のみ表示
                print(f"    - {company}: {count}件")
            if len(company_counts) > 5:
                print(f"    ... 他 {len(company_counts) - 5} 社")
        
        return existing_keys, existing_dict
        
    except Exception as e:
        print(f"⚠️ 既存データ取得時のエラー（新規として扱います）: {e}")
        return set(), {}

def import_accessories(json_file_path, mode='append'):
    """アクセサリーデータをSupabaseにインポート
    
    Args:
        json_file_path: JSONファイルのパス
        mode: 'append' (追加のみ), 'update' (更新), 'replace' (置換)
    """
    print("📚 JSONファイルを読み込み中...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        accessories = json.load(f)
    print(f"📊 {len(accessories)}件のデータを検出")
    
    # Supabaseクライアント取得
    supabase = get_client()
    
    # モードに応じた処理
    if mode == 'replace':
        # 既存データをクリア
        print("🗑️ 既存データをクリア中...")
        try:
            supabase.table('accessories').delete().neq('id', 0).execute()
            existing_keys = set()
            existing_dict = {}
            print("✅ 既存データをクリアしました")
        except Exception as e:
            print(f"⚠️ クリア時のエラー: {e}")
            existing_keys = set()
            existing_dict = {}
    else:
        # 既存データを取得（重複チェック用）
        existing_keys, existing_dict = get_existing_accessories(supabase)
    
    # データ整形と重複チェック
    formatted_accessories = []
    skipped_count = 0
    duplicate_count = 0
    update_count = 0
    duplicates = []
    updates = []
    
    for accessory in accessories:
        # nameがない場合はスキップ
        if not accessory.get('name'):
            skipped_count += 1
            print(f"  ⚠️ スキップ: データに名前がありません")
            continue
        
        # データ整形
        formatted_accessory = {
            'name': accessory.get('name'),
            'company': accessory.get('company') or accessory.get('manufacturer') or '不明'
        }
        
        # その他のフィールドがあれば追加
        if accessory.get('description'):
            formatted_accessory['description'] = accessory.get('description')
        if accessory.get('price'):
            formatted_accessory['price'] = accessory.get('price')
        if accessory.get('url'):
            formatted_accessory['url'] = accessory.get('url')
        
        # 重複チェック用のキーを生成
        key = f"{formatted_accessory['name']}:{formatted_accessory['company']}"
        
        # 重複チェック
        if key in existing_keys:
            if mode == 'update':
                # 更新モード：既存データを更新
                existing_accessory = existing_dict[key]
                formatted_accessory['id'] = existing_accessory['id']  # IDを保持
                updates.append(formatted_accessory)
                update_count += 1
                if update_count <= 3:  # 最初の3件だけ表示
                    print(f"  🔄 更新対象: {formatted_accessory['name']} ({formatted_accessory['company']})")
            else:
                # 追加モード：重複はスキップ
                duplicate_count += 1
                duplicates.append(formatted_accessory)
                if duplicate_count <= 3:  # 最初の3件だけ表示
                    print(f"  ⏭️ 重複スキップ: {formatted_accessory['name']} ({formatted_accessory['company']})")
        else:
            # 新規データ
            formatted_accessories.append(formatted_accessory)
    
    print(f"\n📝 インポート対象: {len(formatted_accessories)}件（新規）")
    if mode == 'update':
        print(f"🔄 更新対象: {update_count}件")
    print(f"⏭️ 重複スキップ: {duplicate_count}件")
    print(f"⚠️ データ不備スキップ: {skipped_count}件\n")
    
    # 重複データの詳細表示（10件まで）
    if duplicates and len(duplicates) > 3:
        print(f"📋 重複データ: 合計 {len(duplicates)}件")
        if len(duplicates) <= 10:
            for dup in duplicates[3:]:  # 4件目以降を表示
                print(f"  - {dup['name']} ({dup['company']})")
    
    # バッチ処理でインポート（新規データ）
    batch_size = 50
    total_imported = 0
    failed_batches = []
    
    if formatted_accessories:
        print("🚀 新規データをインポート中...")
        for i in range(0, len(formatted_accessories), batch_size):
            batch = formatted_accessories[i:i + batch_size]
            try:
                result = supabase.table('accessories').insert(batch).execute()
                total_imported += len(batch)
                print(f"✅ {total_imported}/{len(formatted_accessories)} 件インポート完了")
            except Exception as e:
                print(f"❌ エラー: {e}")
                failed_batches.append({
                    'range': f"{i}〜{i + len(batch)}",
                    'error': str(e),
                    'data': batch
                })
    
    # 更新処理（updateモードの場合）
    total_updated = 0
    if mode == 'update' and updates:
        print("\n🔄 既存データを更新中...")
        for update_accessory in updates:
            try:
                accessory_id = update_accessory.pop('id')
                result = supabase.table('accessories').update(update_accessory).eq('id', accessory_id).execute()
                total_updated += 1
                if total_updated % 10 == 0:
                    print(f"  ✅ {total_updated}/{len(updates)} 件更新完了")
            except Exception as e:
                print(f"❌ 更新エラー: {update_accessory['name']} - {e}")
        
        if total_updated > 0 and total_updated % 10 != 0:
            print(f"  ✅ {total_updated}/{len(updates)} 件更新完了")
    
    # 結果サマリー
    print("\n" + "="*50)
    print("📊 インポート結果サマリー")
    print("="*50)
    print(f"✅ 新規追加: {total_imported}件")
    if mode == 'update':
        print(f"🔄 更新: {total_updated}件")
    print(f"⏭️ 重複スキップ: {duplicate_count}件")
    print(f"❌ 失敗: {len(formatted_accessories) - total_imported}件")
    print(f"⚠️ データ不備: {skipped_count}件")
    
    if failed_batches:
        print("\n❌ 失敗したバッチ:")
        for batch in failed_batches[:5]:  # 最初の5件だけ表示
            print(f"  - {batch['range']}: {batch['error']}")
    
    # メーカー別の集計（新規追加分のみ）
    if total_imported > 0:
        print("\n🏢 メーカー別インポート数（新規）:")
        company_count = {}
        for accessory in formatted_accessories[:total_imported]:
            company = accessory.get('company', '不明')
            company_count[company] = company_count.get(company, 0) + 1
        
        # 上位10社を表示
        for company, count in sorted(company_count.items(), key=lambda x: -x[1])[:10]:
            print(f"  {company}: {count}件")
        
        if len(company_count) > 10:
            print(f"  ... 他 {len(company_count) - 10} 社")
    
    return total_imported, total_updated, duplicate_count

def verify_import():
    """インポート結果を確認"""
    supabase = get_client()
    
    try:
        # 全件数を確認
        result = supabase.table('accessories').select('*', count='exact').execute()
        print(f"\n✅ 総登録数: {result.count}件")
        
        # メーカー別に確認
        all_accessories = supabase.table('accessories').select('company').execute()
        company_count = {}
        for accessory in all_accessories.data:
            company = accessory.get('company', '不明')
            company_count[company] = company_count.get(company, 0) + 1
        
        print("\n🏢 メーカー別登録数:")
        # 上位15社を表示
        for company, count in sorted(company_count.items(), key=lambda x: -x[1])[:15]:
            print(f"  {company}: {count}件")
        
        if len(company_count) > 15:
            total_others = sum(count for company, count in 
                             sorted(company_count.items(), key=lambda x: -x[1])[15:])
            print(f"  その他 {len(company_count) - 15} 社: {total_others}件")
        
        print(f"\n📊 総メーカー数: {len(company_count)}社")
        
    except Exception as e:
        print(f"❌ 確認時のエラー: {e}")

def check_duplicates(json_file_path):
    """インポート前に重複をチェック"""
    print("🔍 重複チェック中...")
    
    # JSONファイルを読み込み
    with open(json_file_path, 'r', encoding='utf-8') as f:
        accessories = json.load(f)
    
    print(f"📄 JSONファイル: {len(accessories)}件")
    
    # Supabaseクライアント取得
    supabase = get_client()
    
    # 既存データを取得
    existing_keys, existing_dict = get_existing_accessories(supabase)
    
    # 重複チェック
    duplicates = []
    new_accessories = []
    
    for accessory in accessories:
        if not accessory.get('name'):
            continue
        
        company = accessory.get('company') or accessory.get('manufacturer') or '不明'
        key = f"{accessory.get('name')}:{company}"
        
        if key in existing_keys:
            duplicates.append({
                'new': accessory,
                'existing': existing_dict[key]
            })
        else:
            new_accessories.append(accessory)
    
    # 結果表示
    print(f"\n📊 チェック結果:")
    print(f"  ✅ 新規追加可能: {len(new_accessories)}件")
    print(f"  ⏭️ 重複: {len(duplicates)}件")
    
    if duplicates and len(duplicates) <= 20:
        print("\n📋 重複データ詳細（最初の20件）:")
        for dup in duplicates[:20]:
            new_item = dup['new']
            existing_item = dup['existing']
            print(f"  - {new_item.get('name')} ({new_item.get('company', '不明')})")
            print(f"    既存ID: {existing_item['id']}")
    elif duplicates:
        print(f"\n📋 重複データが{len(duplicates)}件あります（詳細は省略）")
    
    return new_accessories, duplicates

def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使用方法: python import_accessories.py <JSONファイルパス> [オプション]")
        print("\nオプション:")
        print("  --check   : 重複チェックのみ（インポートしない）")
        print("  --update  : 重複データは更新、新規は追加")
        print("  --replace : 全データを削除して置換")
        print("  (なし)    : 重複をスキップして新規のみ追加（デフォルト）")
        print("\n例:")
        print("  python import_accessories.py data/accessories.json")
        print("  python import_accessories.py data/accessories.json --check")
        print("  python import_accessories.py data/accessories.json --update")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    # ファイル存在確認
    if not os.path.exists(json_file):
        print(f"❌ ファイルが見つかりません: {json_file}")
        sys.exit(1)
    
    # オプション処理
    mode = 'append'  # デフォルトは追加モード
    check_only = False
    
    if len(sys.argv) > 2:
        if sys.argv[2] == '--update':
            mode = 'update'
        elif sys.argv[2] == '--replace':
            mode = 'replace'
        elif sys.argv[2] == '--check':
            check_only = True
    
    if check_only:
        # 重複チェックのみ
        check_duplicates(json_file)
    else:
        # インポート実行
        print(f"📝 モード: {mode}")
        imported, updated, duplicates = import_accessories(json_file, mode)
        
        # 結果確認
        if imported > 0 or updated > 0 or mode == 'replace':
            verify_import()

if __name__ == "__main__":
    main()