#!/usr/bin/env python3
"""PHPファイルの詳細構造を分析"""

from pathlib import Path
import re

def analyze_php_files():
    php_dir = Path('/Users/toru.nakamichi/Desktop/diving_API/data/raw/gear')
    php_files = list(php_dir.glob('*.php'))
    
    print("📄 PHPファイル詳細分析")
    print("=" * 60)
    
    for php_file in php_files:
        print(f"\n📁 {php_file.name}")
        print("-" * 40)
        
        with open(php_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # サンプルデータの表示
        print("【ファイルの最初の1000文字】")
        print(content[:1000])
        print("\n...")
        
        # 配列パターンの検索
        print("\n【配列パターン分析】")
        
        # パターン1: ['key' => 'value'] 形式
        pattern1 = r"\['[^']+'\s*=>\s*'[^']*'\]"
        matches1 = re.findall(pattern1, content)
        if matches1:
            print(f"✅ ['key' => 'value'] 形式: {len(matches1)}個")
            print(f"   サンプル: {matches1[0] if matches1 else ''}")
        
        # パターン2: array(...) 形式の配列
        pattern2 = r"array\s*\([^)]+\)"
        matches2 = re.findall(pattern2, content)
        if matches2:
            print(f"✅ array() 形式: {len(matches2)}個")
        
        # パターン3: 配列の行（提供されたサンプルの形式）
        pattern3 = r"\[\s*'camera'\s*=>\s*'[^']+'"
        matches3 = re.findall(pattern3, content)
        if matches3:
            print(f"✅ camera フィールドを含む配列: {len(matches3)}個")
        
        # 変数名の検索
        var_pattern = r'\$(\w+)\s*='
        variables = re.findall(var_pattern, content)
        if variables:
            print(f"\n【定義されている変数】")
            for var in set(variables):
                print(f"   ${var}")

if __name__ == "__main__":
    analyze_php_files()
