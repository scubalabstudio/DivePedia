#!/usr/bin/env python3
"""
data/raw/systemchart/ の全 PHP ファイルを
data/processed/systemchart/ に JSON として変換するスクリプト

【使用方法】
python3 script/systemchart/convert_all.py

【出力】
ハウジング名をファイル名として出力（例: PT-EP10.json）
"""

import re
import json
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'systemchart'
OUT_DIR = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'systemchart'

ITEM_PATTERN = re.compile(
    r"\[\s*'camera'\s*=>\s*'([^']*)'"
    r",\s*'housing'\s*=>\s*'([^']*)'"
    r",\s*'lens'\s*=>\s*'([^']*)'"
    r",\s*'gear'\s*=>\s*'([^']*)'"
    r",\s*'adapter'\s*=>\s*'([^']*)'"
    r",\s*'extension1'\s*=>\s*'([^']*)'"
    r",\s*'extension2'\s*=>\s*'([^']*)'"
    r",\s*'port'\s*=>\s*'([^']*)'"
    r"\s*\]"
)


def parse_php(text: str) -> list[dict]:
    items = []
    for m in ITEM_PATTERN.finditer(text):
        camera, housing, lens, gear, adapter, ext1, ext2, port = m.groups()
        items.append({
            'camera':     camera or None,
            'housing':    housing or None,
            'lens':       lens or None,
            'gear':       gear or None,
            'adapter':    adapter or None,
            'extension1': ext1 or None,
            'extension2': ext2 or None,
            'port':       port or None,
        })
    return items


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    php_files = sorted(RAW_DIR.glob('*.php'))
    if not php_files:
        print('PHP ファイルが見つかりません')
        return

    for php_file in php_files:
        items = parse_php(php_file.read_text(encoding='utf-8'))
        if not items:
            print(f'  スキップ (パース失敗): {php_file.name}')
            continue

        out_path = OUT_DIR / php_file.with_suffix('.json').name
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

        print(f'  {php_file.name} → {out_path.name} ({len(items)}件)')

    print('\n完了')


if __name__ == '__main__':
    main()
