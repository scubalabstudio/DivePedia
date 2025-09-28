import json
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.supabase import get_client

def import_lights(json_file_path):
    """ライトデータをSupabaseにインポート"""
    print("📚 JSONファイルを読み込み中...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        lights = json.load(f)
    print(f"📊 {len(lights)}件のデータを検出")
    
    # Supabaseクライアント取得
    supabase = get_client()
    
    # 既存データをクリア（オプション）
    print("🗑️ 既存データをクリア中...")
    try:
        supabase.table('lights').delete().neq('id', 0).execute()
    except:
        pass  # テーブルが空の場合はエラーになるので無視
    
    # データ整形（nameが必須）
    formatted_lights = []
    skipped_count = 0
    
    for light in lights:
        if light.get('name'):  # nameがある場合のみ
            formatted_light = {
                'name': light.get('name'),
                'manufacturer': light.get('manufacturer') or light.get('company')
            }
            formatted_lights.append(formatted_light)
        else:
            skipped_count += 1
            print(f"  ⚠️ スキップ: データに名前がありません")
    
    print(f"\n📝 インポート対象: {len(formatted_lights)}件")
    print(f"⏭️ スキップ: {skipped_count}件\n")
    
    # バッチ処理でインポート
    batch_size = 50
    total_imported = 0
    failed_batches = []
    
    for i in range(0, len(formatted_lights), batch_size):
        batch = formatted_lights[i:i + batch_size]
        try:
            result = supabase.table('lights').insert(batch).execute()
            total_imported += len(batch)
            print(f"✅ {total_imported}/{len(formatted_lights)} 件インポート完了")
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
    print(f"❌ 失敗: {len(formatted_lights) - total_imported}件")
    print(f"⏭️ スキップ: {skipped_count}件")
    
    if failed_batches:
        print("\n❌ 失敗したバッチ:")
        for batch in failed_batches:
            print(f"  - {batch['range']}: {batch['error']}")
    
    # メーカー別の集計
    print("\n🏢 メーカー別インポート数:")
    manufacturer_count = {}
    for light in formatted_lights[:total_imported]:
        manufacturer = light.get('manufacturer', '不明')
        manufacturer_count[manufacturer] = manufacturer_count.get(manufacturer, 0) + 1
    
    for manufacturer, count in sorted(manufacturer_count.items()):
        print(f"  {manufacturer}: {count}件")
    
    return total_imported

def verify_import():
    """インポート結果を確認"""
    supabase = get_client()
    
    # 全件数を確認
    result = supabase.table('lights').select('*', count='exact').execute()
    print(f"\n✅ 総登録数: {result.count}件")
    
    # メーカー別に確認
    all_lights = supabase.table('lights').select('manufacturer').execute()
    manufacturer_count = {}
    for light in all_lights.data:
        manufacturer = light.get('manufacturer', '不明')
        manufacturer_count[manufacturer] = manufacturer_count.get(manufacturer, 0) + 1
    
    print("\nメーカー別:")
    for manufacturer, count in sorted(manufacturer_count.items()):
        print(f"  {manufacturer}: {count}件")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        # ファイル存在確認
        if not os.path.exists(json_file):
            print(f"❌ ファイルが見つかりません: {json_file}")
            sys.exit(1)
        
        # インポート実行
        imported = import_lights(json_file)
        
        # 結果確認
        if imported > 0:
            verify_import()
    else:
        print("使用方法: python import_lights.py <JSONファイルパス>")
        print("例: python import_lights.py ../../data/json/lights.json")
