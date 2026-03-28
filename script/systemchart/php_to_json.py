#!/usr/bin/env python3
"""
System Chart PHP to JSON Converter
ダイビング機材のシステムチャートをPHPファイルからJSONファイルに変換するスクリプト

使用方法:
python3 php_to_json.py <php_file> <camera_name> <housing_name>

引数:
- php_file: 変換したいPHPファイルのパス
- camera_name: カメラ名（スペースはアンダースコア_で置換）
- housing_name: ハウジング名（スペースはアンダースコア_で置換）

例:
python3 script/systemchart/php_to_json.py data/raw/gear/canon_n85ef.php "Canon_EF-M" "NA_N85"
python3 script/systemchart/php_to_json.py data/raw/gear/sony_n85_e.php "Sony_Alpha_A7R5" "NA_N85"
python3 script/systemchart/php_to_json.py data/raw/gear/fujifilm_n85_x.php "Fujifilm_XT5" "NA_N85"
python3 script/systemchart/php_to_json.py data/raw/gear/m43_n85.php "Olympus_OM1" "NA_N85"

出力:
- ファイルは data/processed/systemchart/by_camera/{camera_name}.json に出力されます
- JSONにはカメラ、ハウジング、レンズ、ギア、アダプター、エクステンション、ポートの情報が含まれます
"""
import re
import json
import sys
import os

def parse_php_array(php_content, camera_name, housing_name):
    """
    PHPの配列をパースしてJSONに変換する
    
    Args:
        php_content (str): PHPファイルの内容
        camera_name (str): カメラ名（空のフィールドの場合に使用）
        housing_name (str): ハウジング名（空のフィールドの場合に使用）
    
    Returns:
        list: パースされたデータのリスト
    """
    
    # アンダースコアをスペースに置換（JSONの表示用）
    camera_name = camera_name.replace('_', ' ')
    housing_name = housing_name.replace('_', ' ')
    
    # PHPの return [...] ?> パターンを検索
    array_pattern = r'return\s*\[(.*?)\]\s*\?>'
    array_match = re.search(array_pattern, php_content, re.DOTALL)
    
    if not array_match:
        raise ValueError("PHP array not found in file")
    
    array_content = array_match.group(1)
    
    # PHP配列の各要素をパースする正規表現
    # ['camera' => '', 'housing' => '', ...] の形式をマッチ
    item_pattern = r"\[\s*'camera'\s*=>\s*'([^']*)',\s*'housing'\s*=>\s*'([^']*)',\s*'lens'\s*=>\s*'([^']*)',\s*'gear'\s*=>\s*'([^']*)',\s*'adapter'\s*=>\s*'([^']*)',\s*'extension1'\s*=>\s*'([^']*)',\s*'extension2'\s*=>\s*'([^']*)',\s*'port'\s*=>\s*'([^']*)'\s*\]"
    
    items = []
    for match in re.finditer(item_pattern, array_content):
        camera, housing, lens, gear, adapter, extension1, extension2, port = match.groups()
        
        # 空文字列の場合はデフォルト値またはnullを設定
        item = {
            "camera": camera if camera else camera_name,
            "housing": housing if housing else housing_name,
            "lens": lens if lens else None,
            "gear": gear if gear else None,
            "adapter": adapter if adapter else None,
            "extension1": extension1 if extension1 else None,
            "extension2": extension2 if extension2 else None,
            "port": port if port else None
        }
        items.append(item)
    
    return items

def main():
    """
    メイン関数：コマンドライン引数を処理してPHPからJSONへの変換を実行
    """
    # 引数チェック
    if len(sys.argv) != 4:
        print("Usage: python3 php_to_json.py <php_file> <camera_name> <housing_name>")
        print("Note: Use underscores (_) instead of spaces in names. They will be converted to spaces in the JSON.")
        print("Example: python3 php_to_json.py file.php 'NA_XT5' 'Canon_EOS_R5'")
        sys.exit(1)
    
    # コマンドライン引数を取得
    php_file = sys.argv[1]        # 入力PHPファイルパス
    camera_name = sys.argv[2]     # カメラ名（ファイル名にも使用）
    housing_name = sys.argv[3]    # ハウジング名
    
    # ファイル存在チェック
    if not os.path.exists(php_file):
        print(f"Error: File {php_file} not found")
        sys.exit(1)
    
    try:
        # PHPファイルを読み込み（UTF-8エンコーディング）
        with open(php_file, 'r', encoding='utf-8') as f:
            php_content = f.read()
        
        # PHPからJSONへ変換
        items = parse_php_array(php_content, camera_name, housing_name)
        
        # 出力ファイル名を生成（camera_nameを使用、アンダースコア保持）
        output_file = f"{sys.argv[2]}.json"
        output_path = os.path.join("/Users/toru.nakamichi/Desktop/diving_API/data/processed/systemchart/by_camera", output_file)
        
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # JSONファイルに書き出し（日本語文字を保持、インデント付き）
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        
        print(f"Conversion completed: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()