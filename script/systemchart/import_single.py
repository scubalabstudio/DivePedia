#!/usr/bin/env python3
"""
ダイビング機材システムチャートをSupabaseにインポートするスクリプト
マスターデータを最初に一括登録してからシステムチャートを登録します。

【機能】
1. JSONファイルからユニークなアイテム（カメラ、ハウジング、レンズ等）を収集
2. マスターデータテーブルに一括登録
3. システムチャートテーブルに関連データを登録

【使用方法】
python3 import_single.py <json_file_path>

【前提条件】
- .envファイルに以下の環境変数を設定
  SUPABASE_URL=your_supabase_url
  SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
- 必要なPythonパッケージをインストール
  pip install supabase python-dotenv

【使用例】
# Canon EF-Mシステムをインポート
python3 script/systemchart/import_single.py data/processed/systemchart/by_camera/Canon_EF-M.json

# Sony α7R5システムをインポート
python3 script/systemchart/import_single.py data/processed/systemchart/by_camera/Sony_Alpha_A7R5.json

# Olympus OM-1システムをインポート
python3 script/systemchart/import_single.py data/processed/systemchart/by_camera/Olympus_OM1.json

【処理フロー】
1. JSONファイルを読み込み
2. ブランド・モデル名を自動抽出（Canon、Sony、Nauticam等のパターンマッチング）
3. 既存データと重複チェック
4. 新規データのみを各マスターテーブルに挿入
5. 取得したIDを使ってsystem_chartsテーブルに関連データを登録

【対応データ】
- cameras（カメラ）
- housings（ハウジング）
- lenses（レンズ）
- gears（ギア）
- adapters（アダプター）
- extensions（エクステンションリング）
- ports（ポート）
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
    """
    アイテム名からブランドとモデルを抽出する関数
    
    Args:
        item_name (str): アイテムの名前（例: "Canon EOS R5", "NA-C815-Z"）
        item_type (str): アイテムのタイプ（camera/housing/lens/gear/adapter/extension/port）
    
    Returns:
        Tuple[str, str]: (ブランド名, モデル名)のタプル
    
    【対応ブランド例】
    - カメラ: Canon, Nikon, Sony, Olympus, Fujifilm, Panasonic
    - ハウジング: Nauticam (NA), SEA&SEA (MDX/DX), Olympus (PT/UH)
    - レンズ・ギア: Canon, Nikon, Sony, SIGMA, Kenko, Nauticam
    - ポート: Nauticam (NA), SEA&SEA (DX)
    """
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

def collect_unique_items(file_path: str) -> Dict[str, Set[Tuple[str, str]]]:
    """
    JSONファイルからユニークなアイテムを収集し、ブランド・モデル別に整理する関数
    
    Args:
        file_path (str): 処理するJSONファイルのパス
    
    Returns:
        Dict[str, Set[Tuple[str, str]]]: 各カテゴリのユニークな(ブランド, モデル)のセット
    
    【処理内容】
    - JSONファイル内の全レコードをスキャン
    - 各アイテム（camera, housing, lens等）からブランド・モデルを抽出
    - 重複を除去してユニークなアイテムのセットを作成
    """
    items = {
        'cameras': set(),
        'housings': set(),
        'lenses': set(),
        'gears': set(),
        'adapters': set(),
        'extensions': set(),
        'ports': set()
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for record in data:
        # カメラ
        if record.get('camera') and record['camera'] != 'None':
            brand, model = extract_brand_model(record['camera'], 'camera')
            items['cameras'].add((brand, model))
        
        # ハウジング
        if record.get('housing') and record['housing'] != 'None':
            brand, model = extract_brand_model(record['housing'], 'housing')
            items['housings'].add((brand, model))
        
        # レンズ
        if record.get('lens') and record['lens'] != 'None':
            brand, model = extract_brand_model(record['lens'], 'lens')
            items['lenses'].add((brand, model))
        
        # ギア
        if record.get('gear') and record['gear'] != 'None':
            brand, model = extract_brand_model(record['gear'], 'gear')
            items['gears'].add((brand, model))
        
        # アダプター
        if record.get('adapter') and record['adapter'] != 'None':
            brand, model = extract_brand_model(record['adapter'], 'adapter')
            items['adapters'].add((brand, model))
        
        # エクステンション1
        if record.get('extension1') and record['extension1'] != 'None':
            brand, model = extract_brand_model(record['extension1'], 'extension')
            items['extensions'].add((brand, model))
        
        # エクステンション2
        if record.get('extension2') and record['extension2'] != 'None':
            brand, model = extract_brand_model(record['extension2'], 'extension')
            items['extensions'].add((brand, model))
        
        # ポート
        if record.get('port') and record['port'] != 'None':
            brand, model = extract_brand_model(record['port'], 'port')
            items['ports'].add((brand, model))
    
    return items

def insert_master_data(supabase: Client, table_name: str, items: Set[Tuple[str, str]]):
    """
    マスターデータテーブルにユニークなアイテムを一括挿入する関数
    
    Args:
        supabase (Client): Supabaseクライアント
        table_name (str): 対象テーブル名（cameras, housings, lenses等）
        items (Set[Tuple[str, str]]): 挿入する(ブランド, モデル)のセット
    
    Returns:
        Dict[Tuple[str, str], int]: (ブランド, モデル) -> IDのマッピング
    
    【処理フロー】
    1. 既存データをチェック
    2. 新規アイテムのみを抽出
    3. 一括挿入を試行（エラー時は個別挿入にフォールバック）
    4. 挿入結果のIDマッピングを返却
    """
    if not items:
        print(f"  {table_name}: 挿入するデータなし")
        return {}
    
    print(f"  {table_name}: {len(items)}件のユニークなアイテムを処理中...")
    
    # 既存データを確認
    existing = supabase.table(table_name).select('id, brand, model').execute()
    existing_items = {(row['brand'], row['model']): row['id'] for row in existing.data}
    
    # 新規挿入が必要なアイテム
    new_items = []
    item_to_id = {}
    
    for brand, model in items:
        if (brand, model) in existing_items:
            item_to_id[(brand, model)] = existing_items[(brand, model)]
            print(f"    既存: {brand} {model}")
        else:
            new_items.append({'brand': brand, 'model': model})
    
    # 新規アイテムを一括挿入
    if new_items:
        try:
            result = supabase.table(table_name).insert(new_items).execute()
            for item_data in result.data:
                item_to_id[(item_data['brand'], item_data['model'])] = item_data['id']
                print(f"    新規挿入: {item_data['brand']} {item_data['model']}")
        except Exception as e:
            print(f"    一括挿入エラー: {e}")
            # 個別挿入にフォールバック
            for item in new_items:
                try:
                    result = supabase.table(table_name).insert(item).execute()
                    if result.data:
                        item_to_id[(item['brand'], item['model'])] = result.data[0]['id']
                        print(f"    個別挿入: {item['brand']} {item['model']}")
                except Exception as e:
                    print(f"    個別挿入エラー: {item['brand']} {item['model']} - {e}")
    
    print(f"  {table_name}完了: 合計{len(item_to_id)}件")
    return item_to_id

def process_file_with_master_data(file_path: str, supabase: Client):
    """
    マスターデータを登録後、システムチャートデータを処理する関数
    
    Args:
        file_path (str): 処理するJSONファイルのパス
        supabase (Client): Supabaseクライアント
    
    【3段階の処理】
    Step 1: ユニークなアイテムを収集
    Step 2: マスターデータを一括登録
    Step 3: システムチャートに関連データを登録
    
    【重複チェック】
    - 既存のsystem_chartsテーブルと照合
    - 同一構成は重複として除外
    
    【エラーハンドリング】
    - 各レコードで個別にエラーハンドリング
    - 一部失敗でも処理継続
    - 最終的に成功/失敗件数を表示
    """
    print(f"Processing file: {file_path}")
    
    # Step 1: ユニークなアイテムを収集
    print("\n=== Step 1: ユニークなアイテムを収集中 ===")
    unique_items = collect_unique_items(file_path)
    
    for table_name, items in unique_items.items():
        print(f"  {table_name}: {len(items)}件")
    
    # Step 2: マスターデータを一括登録
    print("\n=== Step 2: マスターデータを一括登録中 ===")
    master_data_map = {}
    
    for table_name, items in unique_items.items():
        master_data_map[table_name] = insert_master_data(supabase, table_name, items)
    
    # Step 3: システムチャートを登録
    print("\n=== Step 3: システムチャートを登録中 ===")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    success_count = 0
    error_count = 0
    
    for i, record in enumerate(data):
        try:
            print(f"Processing record {i+1}/{len(data)}")
            
            # 各アイテムのIDを取得
            camera_id = None
            if record.get('camera') and record['camera'] != 'None':
                brand, model = extract_brand_model(record['camera'], 'camera')
                camera_id = master_data_map['cameras'].get((brand, model))
            
            housing_id = None
            if record.get('housing') and record['housing'] != 'None':
                brand, model = extract_brand_model(record['housing'], 'housing')
                housing_id = master_data_map['housings'].get((brand, model))
            
            lens_id = None
            if record.get('lens') and record['lens'] != 'None':
                brand, model = extract_brand_model(record['lens'], 'lens')
                lens_id = master_data_map['lenses'].get((brand, model))
            
            gear_id = None
            if record.get('gear') and record['gear'] != 'None':
                brand, model = extract_brand_model(record['gear'], 'gear')
                gear_id = master_data_map['gears'].get((brand, model))
            
            adapter_id = None
            if record.get('adapter') and record['adapter'] != 'None':
                brand, model = extract_brand_model(record['adapter'], 'adapter')
                adapter_id = master_data_map['adapters'].get((brand, model))
            
            extension1_id = None
            if record.get('extension1') and record['extension1'] != 'None':
                brand, model = extract_brand_model(record['extension1'], 'extension')
                extension1_id = master_data_map['extensions'].get((brand, model))
            
            extension2_id = None
            if record.get('extension2') and record['extension2'] != 'None':
                brand, model = extract_brand_model(record['extension2'], 'extension')
                extension2_id = master_data_map['extensions'].get((brand, model))
            
            port_id = None
            if record.get('port') and record['port'] != 'None':
                brand, model = extract_brand_model(record['port'], 'port')
                port_id = master_data_map['ports'].get((brand, model))
            
            # システムチャートレコード作成
            system_chart_data = {
                'camera_id': camera_id,
                'housing_id': housing_id,
                'lens_id': lens_id,
                'gear_id': gear_id,
                'adapter_id': adapter_id,
                'extension1_id': extension1_id,
                'extension2_id': extension2_id,
                'port_id': port_id
            }
            
            # NULL値を除去
            system_chart_data = {k: v for k, v in system_chart_data.items() if v is not None}
            
            if len(system_chart_data) < 2:  # 最低2つの要素が必要
                print(f"    スキップ: 有効な要素が不足 (record {i+1})")
                continue
            
            # 重複チェック
            query = supabase.table('system_charts').select('id')
            for key, value in system_chart_data.items():
                query = query.eq(key, value)
            
            existing = query.execute()
            
            if existing.data:
                print(f"    重複スキップ: record {i+1}")
                continue
            
            # システムチャートに挿入
            result = supabase.table('system_charts').insert(system_chart_data).execute()
            
            if result.data:
                success_count += 1
                print(f"    成功: record {i+1}")
            else:
                error_count += 1
                print(f"    失敗: record {i+1}")
            
        except Exception as e:
            error_count += 1
            print(f"    エラー (record {i+1}): {e}")
            continue
    
    print(f"\n=== 処理完了 ===")
    print(f"成功: {success_count}件")
    print(f"エラー: {error_count}件")
    print(f"合計: {len(data)}件")

def main():
    """
    メイン実行関数
    
    【実行時引数チェック】
    - JSONファイルパスが正しく指定されているかチェック
    - ファイルの存在確認
    
    【環境変数チェック】
    - SUPABASE_URL
    - SUPABASE_SERVICE_ROLE_KEY
    
    【実行例】
    python3 import_single.py data/processed/systemchart/by_camera/Canon_EF-M.json
    """
    if len(sys.argv) != 2:
        print("Usage: python3 import_single.py <json_file_path>")
        print("Example: python3 import_single.py data/processed/systemchart/by_camera/Canon_EF-M.json")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    # 環境変数からsupabase設定を取得
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("Error: SUPABASE_URL と SUPABASE_SERVICE_ROLE_KEY 環境変数を設定してください")
        sys.exit(1)
    
    print(f"Connecting to Supabase: {url}")
    supabase: Client = create_client(url, key)
    
    print(f"\n=== マスターデータ優先インポート開始 ===")
    process_file_with_master_data(file_path, supabase)

if __name__ == "__main__":
    main()