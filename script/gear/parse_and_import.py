#!/usr/bin/env python3
"""
PHPシステムチャートファイルを解析してSupabaseにインポート（修正版）
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional

# プロジェクトルートをパスに追加
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
sys.path.insert(0, str(project_root))

print(f"📁 プロジェクトルート: {project_root}")

try:
    from config.supabase import get_client
    print("✅ config.supabase インポート成功")
except ImportError as e:
    print(f"❌ config.supabase インポートエラー: {e}")
    sys.exit(1)

class PHPSystemChartParser:
    """PHPファイルからシステムチャートデータを抽出（改良版）"""
    
    def parse_php_file(self, file_path: Path) -> List[Dict]:
        """PHPファイルを解析してデータを抽出"""
        print(f"\n📄 解析中: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 複数のパターンで試す
        data = []
        
        # パターン1: 提供されたサンプル形式
        # ['camera' => 'OM SYSTEM OM1', 'housing' => 'UH-OM1 II', ...]
        pattern1 = r"\[\s*'camera'\s*=>\s*'([^']*)'[^]]*'housing'\s*=>\s*'([^']*)'[^]]*'lens'\s*=>\s*'([^']*)'[^]]*'gear'\s*=>\s*'([^']*)'[^]]*'adapter'\s*=>\s*'([^']*)'[^]]*'extension2'\s*=>\s*'([^']*)'[^]]*'extension1'\s*=>\s*'([^']*)'[^]]*'port'\s*=>\s*'([^']*)'\s*\]"
        
        matches = re.findall(pattern1, content)
        if matches:
            print(f"   ✅ パターン1で {len(matches)}件のデータを発見")
            for match in matches:
                data.append({
                    'camera': match[0] if match[0] else None,
                    'housing': match[1] if match[1] else None,
                    'lens': match[2] if match[2] else None,
                    'gear': match[3] if match[3] else None,
                    'adapter': match[4] if match[4] else None,
                    'extension2': match[5] if match[5] else None,
                    'extension1': match[6] if match[6] else None,
                    'port': match[7] if match[7] else None
                })
        
        # パターン2: より柔軟な抽出
        if not data:
            data = self.extract_flexible_format(content)
        
        print(f"   ✅ 合計 {len(data)}件のデータを抽出")
        return data
    
    def extract_flexible_format(self, content: str) -> List[Dict]:
        """より柔軟な形式でデータを抽出"""
        data = []
        
        # 各配列要素を個別に抽出
        # [...] で囲まれた部分を探す
        array_pattern = r'\[[^\]]*(?:camera|housing|lens)[^\]]*\]'
        arrays = re.findall(array_pattern, content, re.IGNORECASE)
        
        for array_str in arrays:
            item = {}
            
            # 各フィールドを抽出
            fields = {
                'camera': r"'camera'\s*=>\s*'([^']*)'",
                'housing': r"'housing'\s*=>\s*'([^']*)'",
                'lens': r"'lens'\s*=>\s*'([^']*)'",
                'gear': r"'gear'\s*=>\s*'([^']*)'",
                'adapter': r"'adapter'\s*=>\s*'([^']*)'",
                'extension1': r"'extension1'\s*=>\s*'([^']*)'",
                'extension2': r"'extension2'\s*=>\s*'([^']*)'",
                'port': r"'port'\s*=>\s*'([^']*)'",
            }
            
            for field, pattern in fields.items():
                match = re.search(pattern, array_str)
                if match:
                    value = match.group(1)
                    item[field] = value if value else None
            
            if item and ('camera' in item or 'housing' in item or 'lens' in item):
                data.append(item)
        
        return data

class SystemChartImporter:
    """システムチャートをSupabaseにインポート"""
    
    def __init__(self):
        self.supabase = get_client()
        self.cache = {
            'cameras': {},
            'housings': {},
            'lenses': {},
            'ports': {},
            'gears': {},
            'adapters': {},
            'extensions': {}
        }
    
    def get_or_create_item(self, table: str, model: str) -> Optional[int]:
        """アイテムを取得または作成"""
        if not model or model == 'NULL' or model == '':
            return None
        
        # キャッシュチェック
        if model in self.cache[table]:
            return self.cache[table][model]
        
        try:
            # 既存データチェック
            result = self.supabase.table(table).select('id').eq('model', model).execute()
            
            if result.data:
                item_id = result.data[0]['id']
            else:
                # 新規作成
                result = self.supabase.table(table).insert({
                    'model': model,
                    'brand': self.extract_brand(model)
                }).execute()
                item_id = result.data[0]['id']
                print(f"      ✅ 新規登録: {table} - {model}")
            
            self.cache[table][model] = item_id
            return item_id
            
        except Exception as e:
            print(f"      ❌ エラー ({table}): {e}")
            return None
    
    def extract_brand(self, model: str) -> Optional[str]:
        """モデル名からブランドを推測"""
        brands = {
            'OM SYSTEM': ['OM SYSTEM', 'OM1', 'OM5'],
            'Olympus': ['Olympus', 'M.ZUIKO'],
            'AOI': ['AOI', 'UH-', 'FLP-', 'DLP-'],
            'Sea&Sea': ['Sea&Sea', 'MDX-', 'YS-'],
            'TG': ['TG-', 'PT-'],
            'Canon': ['Canon', 'EOS', 'RF', 'EF'],
            'Nikon': ['Nikon', 'NIKKOR', 'Z'],
            'Sony': ['Sony', 'α', 'FE', 'E'],
        }
        
        if model:
            model_upper = model.upper()
            for brand, keywords in brands.items():
                for keyword in keywords:
                    if keyword.upper() in model_upper:
                        return brand
        
        return None
    
    def import_charts(self, charts: List[Dict]) -> Dict:
        """チャートデータをインポート"""
        stats = {'success': 0, 'skip': 0, 'error': 0}
        
        for i, chart in enumerate(charts, 1):
            print(f"\n   [{i}/{len(charts)}] 処理中...")
            
            # デバッグ情報
            print(f"      Camera: {chart.get('camera', 'N/A')}")
            print(f"      Lens: {chart.get('lens', 'N/A')}")
            
            # 各アイテムのIDを取得
            chart_data = {}
            
            if chart.get('camera'):
                chart_data['camera_id'] = self.get_or_create_item('cameras', chart['camera'])
            
            if chart.get('housing'):
                chart_data['housing_id'] = self.get_or_create_item('housings', chart['housing'])
            
            if chart.get('lens'):
                chart_data['lens_id'] = self.get_or_create_item('lenses', chart['lens'])
            
            if chart.get('port'):
                chart_data['port_id'] = self.get_or_create_item('ports', chart['port'])
            
            if chart.get('gear'):
                chart_data['gear_id'] = self.get_or_create_item('gears', chart['gear'])
            
            if chart.get('adapter'):
                chart_data['adapter_id'] = self.get_or_create_item('adapters', chart['adapter'])
            
            if chart.get('extension1'):
                chart_data['extension1_id'] = self.get_or_create_item('extensions', chart['extension1'])
            
            if chart.get('extension2'):
                chart_data['extension2_id'] = self.get_or_create_item('extensions', chart['extension2'])
            
            # システムチャートに登録
            if chart_data:
                try:
                    result = self.supabase.table('system_charts').insert(chart_data).execute()
                    stats['success'] += 1
                    print(f"      ✅ システムチャート登録成功")
                except Exception as e:
                    if 'duplicate' in str(e).lower():
                        stats['skip'] += 1
                        print(f"      ⏭️ スキップ（重複）")
                    else:
                        stats['error'] += 1
                        print(f"      ❌ エラー: {e}")
        
        return stats

def main():
    """メイン処理"""
    print("🚀 PHPシステムチャートインポート開始（改良版）")
    print("=" * 60)
    
    # PHPファイルのディレクトリ
    php_dir = Path('/Users/toru.nakamichi/Desktop/diving_API/data/raw/gear')
    php_files = list(php_dir.glob('*.php'))
    
    if not php_files:
        print(f"❌ PHPファイルが見つかりません: {php_dir}")
        return
    
    print(f"📁 対象ディレクトリ: {php_dir}")
    print(f"📄 PHPファイル数: {len(php_files)}個")
    for f in php_files:
        print(f"   - {f.name}")
    
    # パーサーとインポーターの初期化
    parser = PHPSystemChartParser()
    importer = SystemChartImporter()
    
    all_charts = []
    
    # 各PHPファイルを解析
    for php_file in php_files:
        charts = parser.parse_php_file(php_file)
        all_charts.extend(charts)
    
    print(f"\n📊 合計: {len(all_charts)}件のデータを抽出")
    
    if all_charts:
        # JSONファイルに保存（確認用）
        output_file = php_dir / 'extracted_system_charts.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_charts, f, ensure_ascii=False, indent=2)
        print(f"💾 バックアップ保存: {output_file}")
        
        # 最初の3件を表示
        print("\n📋 抽出データサンプル（最初の3件）:")
        for i, chart in enumerate(all_charts[:3], 1):
            print(f"\n  [{i}]")
            for key, value in chart.items():
                if value:
                    print(f"    {key}: {value}")
        
        # インポート確認
        response = input("\n📤 Supabaseにインポートしますか？ (y/n): ")
        if response.lower() == 'y':
            stats = importer.import_charts(all_charts)
            
            print("\n" + "=" * 60)
            print("📊 インポート結果:")
            print(f"  ✅ 成功: {stats['success']}件")
            print(f"  ⏭️ スキップ: {stats['skip']}件")
            print(f"  ❌ エラー: {stats['error']}件")
            
            print("\n📦 登録されたマスターデータ:")
            for table, cache in importer.cache.items():
                if cache:
                    print(f"  {table}: {len(cache)}件")
    
    print("\n✨ 処理完了!")

if __name__ == "__main__":
    main()
