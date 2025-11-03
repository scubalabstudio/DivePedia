#!/usr/bin/env python3
"""
要件に従ったデータインポートスクリプト:
1. 各項目(camera,housing,lens,gear等)を各テーブルに格納（nameはユニーク、既存は스キップ）
2. 全てのマスターデータ格納後、IDを使ってシステムチャートテーブルに挿入
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, Set, Tuple, Optional
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

def extract_brand_model(item_name: str, item_type: str) -> Tuple[str, str]:
    """アイテム名からブランドとモデルを抽出"""
    if not item_name or item_name == 'None':
        return "", ""
    
    item_name = item_name.strip()
    
    # カメラ用パターン
    if item_type == 'camera':
        camera_patterns = {
            'Canon': r'^Canon\s+(.*)',
            'Nikon': r'^Nikon\s+(.*)', 
            'Sony': r'^Sony\s+(.*)',
            'SONY': r'^SONY\s+(.*)',
            'Olympus': r'^Olympus\s+(.*)',
            'OM SYSTEM': r'^OM SYSTEM\s+(.*)',
            'Fujifilm': r'^Fujifilm\s+(.*)',
            'Panasonic': r'^Panasonic\s+(.*)',
        }
        
        for brand, pattern in camera_patterns.items():
            match = re.match(pattern, item_name, re.IGNORECASE)
            if match:
                return brand, match.group(1).strip()
        
        # 特殊ケース
        if item_name.startswith(('TG-', 'E-', 'OM-D')):
            return 'Olympus', item_name
    
    # ハウジング用パターン  
    elif item_type == 'housing':
        if item_name.startswith(('MDX-', 'DX-')):
            return 'SEA&SEA', item_name
        elif item_name.startswith('NA '):
            return 'Nauticam', item_name
        elif item_name.startswith('PT-'):
            return 'Olympus', item_name
        elif item_name.startswith('UH-'):
            return 'Olympus', item_name
    
    # ポート用パターン
    elif item_type == 'port':
        if item_name.startswith(('DX', 'オプティカル')):
            return 'SEA&SEA', item_name
        elif item_name.startswith('NA '):
            return 'Nauticam', item_name
    
    # エクステンション用パターン
    elif item_type == 'extension':
        if item_name.startswith('DX'):
            return 'SEA&SEA', item_name
        elif item_name.startswith('NA '):
            return 'Nauticam', item_name
        elif item_name.startswith('ER-'):
            return 'SEA&SEA', item_name
    
    # レンズ・ギア用共通パターン
    if item_type in ['lens', 'gear']:
        brand_patterns = {
            'Canon': r'^Canon\s+(.*)',
            'Nikon': r'^Nikon\s+(.*)',
            'Sony': r'^Sony\s+(.*)',
            'SIGMA': r'^SIGMA\s*(.*)',
            'Kenko': r'^Kenko\s+(.*)',
            'Nauticam': r'^NA-(.*)',
        }
        
        for brand, pattern in brand_patterns.items():
            match = re.match(pattern, item_name, re.IGNORECASE)
            if match:
                return brand, match.group(1).strip() if match.group(1).strip() else item_name
    
    return "", item_name

def collect_all_items(data_dir: str) -> Dict[str, Set[str]]:
    """
    全てのJSONファイルから各項目を収集
    
    Returns:
        Dict[table_name, Set[item_names]]: テーブル名とアイテム名のセット
    """
    items = {
        'cameras': set(),
        'housings': set(), 
        'lenses': set(),
        'gears': set(),
        'adapters': set(),
        'extensions': set(),
        'ports': set(),
    }
    
    camera_dir = os.path.join(data_dir, "camera")
    
    if not os.path.exists(camera_dir):
        print(f"Error: {camera_dir} が存在しません")
        return items
    
    json_files = [f for f in os.listdir(camera_dir) if f.endswith('.json')]
    print(f"Processing {len(json_files)} files to collect items...")
    
    for filename in json_files:
        file_path = os.path.join(camera_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for record in data:
                    # 各項目を収集
                    if record.get('camera'):
                        items['cameras'].add(record['camera'])
                    
                    if record.get('housing'):
                        items['housings'].add(record['housing'])
                    
                    if record.get('lens') and record['lens'] != 'None':
                        items['lenses'].add(record['lens'])
                    
                    if record.get('gear') and record['gear'] != 'None':
                        items['gears'].add(record['gear'])
                    
                    if record.get('adapter') and record['adapter'] != 'None':
                        items['adapters'].add(record['adapter'])
                    
                    # エクステンション（複数フィールド）
                    for ext_key in ['extension1', 'extension2', 'extension3']:
                        if record.get(ext_key) and record[ext_key] != 'None':
                            items['extensions'].add(record[ext_key])
                    
                    if record.get('port') and record['port'] != 'None':
                        items['ports'].add(record['port'])
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    return items

def insert_or_get_item(item_name: str, table_name: str, item_type: str, supabase: Client) -> Optional[int]:
    """
    アイテムをテーブルに挿入、または既存のIDを取得
    
    Args:
        item_name: アイテム名
        table_name: テーブル名
        item_type: アイテムタイプ
        supabase: supabaseクライアント
    
    Returns:
        int: アイテムのID (失敗時はNone)
    """
    if not item_name or item_name == 'None':
        return None
    
    try:
        # 既存チェック（フル名で検索）
        existing = supabase.table(table_name).select('id').eq('model', item_name).execute()
        
        if existing.data:
            return existing.data[0]['id']
        
        # ブランドとモデルを抽出
        brand, model = extract_brand_model(item_name, item_type)
        
        # カメラの場合、modelはブランドを除いた部分のみ
        if item_type == 'camera':
            model_to_store = model
        else:
            model_to_store = item_name  # カメラ以外はフル名を保存
        
        # 既存チェック（model名で再検索）
        existing_model = supabase.table(table_name).select('id').eq('model', model_to_store).execute()
        
        if existing_model.data:
            return existing_model.data[0]['id']
        
        # 新規挿入
        result = supabase.table(table_name).insert({
            'model': model_to_store,
            'brand': brand if brand else None
        }).execute()
        
        if result.data:
            return result.data[0]['id']
        
    except Exception as e:
        print(f"Error inserting/getting {item_name} from {table_name}: {e}")
    
    return None

def insert_master_data(items: Dict[str, Set[str]], supabase: Client) -> Dict[str, Dict[str, int]]:
    """
    全てのマスターデータを各テーブルに挿入
    
    Returns:
        Dict[table_name, Dict[item_name, id]]: テーブル名 -> {アイテム名: ID} のマッピング
    """
    print("\n=== マスターデータ挿入開始 ===")
    
    id_mappings = {}
    
    table_types = {
        'cameras': 'camera',
        'housings': 'housing',
        'lenses': 'lens',
        'gears': 'gear',
        'adapters': 'adapter',
        'extensions': 'extension',
        'ports': 'port',
    }
    
    for table_name, item_type in table_types.items():
        if not items[table_name]:
            id_mappings[table_name] = {}
            continue
            
        print(f"\n{table_name}テーブルに{len(items[table_name])}個のアイテムを処理中...")
        id_mappings[table_name] = {}
        
        processed = 0
        for item_name in sorted(items[table_name]):
            item_id = insert_or_get_item(item_name, table_name, item_type, supabase)
            if item_id:
                id_mappings[table_name][item_name] = item_id
            
            processed += 1
            if processed % 50 == 0:
                print(f"  {processed}/{len(items[table_name])}件処理済み...")
        
        print(f"{table_name}完了: {len(id_mappings[table_name])}件")
    
    return id_mappings

def insert_system_charts(data_dir: str, id_mappings: Dict[str, Dict[str, int]], supabase: Client):
    """
    システムチャートデータを挿入
    """
    camera_dir = os.path.join(data_dir, "camera")
    
    print(f"\n=== システムチャートデータ挿入開始 ===")
    
    chart_count = 0
    error_count = 0
    
    json_files = [f for f in os.listdir(camera_dir) if f.endswith('.json')]
    
    for file_index, filename in enumerate(json_files, 1):
        file_path = os.path.join(camera_dir, filename)
        print(f"[{file_index}/{len(json_files)}] Processing: {filename}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for record in data:
                    # 各項目のIDを取得
                    camera_id = id_mappings['cameras'].get(record.get('camera'))
                    housing_id = id_mappings['housings'].get(record.get('housing'))
                    lens_id = id_mappings['lenses'].get(record.get('lens'))
                    gear_id = id_mappings['gears'].get(record.get('gear'))
                    adapter_id = id_mappings['adapters'].get(record.get('adapter'))
                    extension1_id = id_mappings['extensions'].get(record.get('extension1'))
                    extension2_id = id_mappings['extensions'].get(record.get('extension2'))
                    extension3_id = id_mappings['extensions'].get(record.get('extension3'))
                    port_id = id_mappings['ports'].get(record.get('port'))
                    
                    # 必須項目チェック（camera + housing）
                    if not (camera_id and housing_id):
                        error_count += 1
                        continue
                    
                    # システムチャートレコードを作成
                    chart_data = {
                        'camera_id': camera_id,
                        'housing_id': housing_id,
                    }
                    
                    # オプション項目を追加
                    if lens_id:
                        chart_data['lens_id'] = lens_id
                    if gear_id:
                        chart_data['gear_id'] = gear_id
                    if adapter_id:
                        chart_data['adapter_id'] = adapter_id
                    if extension1_id:
                        chart_data['extension1_id'] = extension1_id
                    if extension2_id:
                        chart_data['extension2_id'] = extension2_id
                    if extension3_id:
                        chart_data['extension3_id'] = extension3_id
                    if port_id:
                        chart_data['port_id'] = port_id
                    
                    try:
                        result = supabase.table('system_charts').insert(chart_data).execute()
                        chart_count += 1
                        
                        if chart_count % 500 == 0:
                            print(f"  Processed {chart_count} system charts...")
                            
                    except Exception as e:
                        error_count += 1
                        if error_count <= 5:  # 最初の5つのエラーのみ表示
                            print(f"Error inserting system chart: {e}")
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    print(f"システムチャート完了: {chart_count}件挿入, {error_count}件エラー")

def main():
    # 環境変数からsupabase設定を取得
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not key:
        print("Error: SUPABASE_URL と SUPABASE_ANON_KEY 環境変数を設定してください")
        sys.exit(1)
    
    print(f"Connecting to Supabase: {url}")
    supabase: Client = create_client(url, key)
    
    # データディレクトリを設定
    data_dir = os.path.join(os.path.dirname(__file__), '../../data/processed/systemchart')
    
    if not os.path.exists(data_dir):
        print(f"Error: {data_dir} が存在しません")
        sys.exit(1)
    
    print(f"Data directory: {data_dir}")
    
    # 全アイテムを収集
    print("\n=== アイテム収集開始 ===")
    items = collect_all_items(data_dir)
    
    # 統計表示
    print("\n=== 収集統計 ===")
    for table_name, item_set in items.items():
        print(f"{table_name}: {len(item_set)}個")
    
    # マスターデータを挿入
    id_mappings = insert_master_data(items, supabase)
    
    # システムチャートを挿入
    insert_system_charts(data_dir, id_mappings, supabase)
    
    # 最終確認
    try:
        final_result = supabase.table('system_charts').select('id', count='exact').execute()
        final_count = final_result.count if hasattr(final_result, 'count') else len(final_result.data)
        print(f"\n最終システムチャート数: {final_count}件")
    except Exception as e:
        print(f"Error getting final count: {e}")
    
    print("\n=== インポート完了 ===")

if __name__ == "__main__":
    main()