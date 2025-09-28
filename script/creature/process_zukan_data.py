#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process and categorize the zukan creature data
"""

import json
import re
import os

def load_test_data():
    """Load the test sample data"""
    with open("../../data/processed/creature/zukan_test_sample.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def categorize_creature(name, group_name=""):
    """Improved categorization based on name and group context"""
    
    # Fish patterns - comprehensive
    fish_patterns = [
        r'.*[魚フグハゼダイキスイワシサバアジマグロタイ]$',
        r'.*[ベラカワハギフエダイニザダイキンチャクダイスズメダイ]$',
        r'.*[チョウチョウウオハタネンブツダイヒメジアンコウ]$',
        r'.*[エソギンポイワシアナゴウツボカサゴコチ]$',
        r'.*[ブダイボラカマスホウボウゴンベトラギス]$',
        r'.*[カレイヒラメキンメダイテンジクダイ]$',
        r'.*[バンク|ダルマハゼ|スズメダイ|チョウチョウウオ].*'
    ]
    
    # Crustacean patterns - detailed
    crustacean_patterns = [
        r'.*[エビカニヤドカリシャコ]$',
        r'.*[ガニザリ]$',
        r'.*(オキアミ|アミ|ヨコエビ|ワレカラ|カイカムリ).*',
        r'.*(カクレエビ|コシオリエビ|テッポウエビ|モエビ).*',
        r'.*(クモガニ|ワタリガニ|イワガニ|スナガニ).*'
    ]
    
    # Sea slug and mollusk patterns
    sea_slug_patterns = [
        r'.*ウミウシ.*',
        r'.*アメフラシ.*',
        r'.*クリオネ.*',
        r'.*ミノウミウシ.*',
        r'.*ガイ$',
        r'.*貝.*',
        r'.*コチョウ.*'
    ]
    
    # Other marine life patterns
    other_patterns = [
        r'.*[クラゲイカタコ].*',
        r'.*[ヒトデウニナマコ].*',
        r'.*[サンゴイソギンチャク].*',
        r'.*[ホヤクジラアザラシ].*',
        r'.*[アザラシラッコイルカ].*'
    ]
    
    # Use group context for better categorization
    group_lower = group_name.lower()
    
    if any(word in group_lower for word in ['エビ', 'カニ', 'ヤドカリ', '甲殻']):
        return 'crustacean'
    elif any(word in group_lower for word in ['ウミウシ', '巻貝', '貝']):
        return 'sea_slug'
    elif any(word in group_lower for word in ['ハゼ', 'スズメダイ', 'チョウチョウウオ', 'ダイ', '魚']):
        return 'fish'
    
    # Pattern-based categorization
    for pattern in fish_patterns:
        if re.match(pattern, name):
            return 'fish'
    
    for pattern in crustacean_patterns:
        if re.match(pattern, name):
            return 'crustacean'
    
    for pattern in sea_slug_patterns:
        if re.match(pattern, name):
            return 'sea_slug'
    
    for pattern in other_patterns:
        if re.match(pattern, name):
            return 'other'
    
    # Default based on name characteristics
    if any(char in name for char in ['魚', 'ダイ', 'ハゼ']):
        return 'fish'
    elif any(char in name for char in ['エビ', 'カニ']):
        return 'crustacean'
    elif any(char in name for char in ['ウシ', 'ガイ']):
        return 'sea_slug'
    
    return 'other'

def filter_valid_creatures(creatures):
    """Filter out invalid or non-creature entries"""
    valid_creatures = []
    
    # Skip words that are clearly not creature names
    skip_patterns = [
        r'^(ア|イ|ウ|エ|オ|カ|ガ|キ|ギ|ク|グ|ケ|ゲ|コ|ゴ|サ|ザ|シ|ジ|ス|ズ|セ|ゼ|ソ|ゾ|タ|ダ|チ|ヂ|ツ|ヅ|テ|デ|ト|ド|ナ|ニ|ヌ|ネ|ノ|ハ|バ|パ|ヒ|ビ|ピ|フ|ブ|プ|ヘ|ベ|ペ|ホ|ボ|ポ|マ|ミ|ム|メ|モ|ヤ|ユ|ヨ|ラ|リ|ル|レ|ロ|ワ|ヲ|ン)$',  # Single characters
        r'^.{1}$',  # Single character
        r'^.{50,}$',  # Too long
        r'.*ホーム.*',
        r'.*メニュー.*',
        r'.*ナビ.*',
        r'.*サイト.*',
        r'.*ページ.*',
        r'.*一覧.*',
        r'.*リスト.*',
        r'.*検索.*'
    ]
    
    for creature in creatures:
        name = creature['name']
        
        # Skip if matches any skip pattern
        if any(re.match(pattern, name) for pattern in skip_patterns):
            continue
        
        # Skip if not primarily Japanese characters
        if not re.match(r'^[ひらがなカタカナ漢字ー・（）\w\s]+$', name):
            continue
        
        # Must be reasonable length
        if not (2 <= len(name) <= 30):
            continue
        
        valid_creatures.append(creature)
    
    return valid_creatures

def process_and_save_data():
    """Process the test data and save categorized results"""
    
    print("Loading test data...")
    creatures = load_test_data()
    print(f"Loaded {len(creatures)} creatures")
    
    # Filter valid creatures
    print("Filtering valid creatures...")
    valid_creatures = filter_valid_creatures(creatures)
    print(f"Valid creatures after filtering: {len(valid_creatures)}")
    
    # Categorize creatures
    print("Categorizing creatures...")
    categories = {'fish': [], 'crustacean': [], 'sea_slug': [], 'other': []}
    
    for creature in valid_creatures:
        category = categorize_creature(creature['name'], creature.get('group_name', ''))
        creature['category'] = category
        categories[category].append(creature)
    
    # Print categorization summary
    print("\nCategorization summary:")
    for category, items in categories.items():
        print(f"{category}: {len(items)} creatures")
    
    # Save each category separately
    base_path = "../../data/processed/creature/"
    os.makedirs(base_path, exist_ok=True)
    
    for category, items in categories.items():
        if items:
            # Re-assign IDs within category
            for i, item in enumerate(items, 1):
                item['id'] = i
                # Remove group info to match existing data format
                clean_item = {'id': item['id'], 'name': item['name']}
                items[i-1] = clean_item
            
            filename = f"{base_path}zukan_{category}_data.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(items)} {category} creatures to {filename}")
    
    # Save all creatures in one file (with categories)
    all_creatures_with_categories = []
    creature_id = 1
    for category, items in categories.items():
        for item in items:
            all_creatures_with_categories.append({
                'id': creature_id,
                'name': item['name'],
                'category': category
            })
            creature_id += 1
    
    all_filename = f"{base_path}zukan_all_creatures_categorized.json"
    with open(all_filename, 'w', encoding='utf-8') as f:
        json.dump(all_creatures_with_categories, f, ensure_ascii=False, indent=2)
    print(f"Saved all {len(all_creatures_with_categories)} categorized creatures to {all_filename}")
    
    # Show samples from each category
    print("\nSample creatures by category:")
    for category, items in categories.items():
        if items:
            print(f"\n{category.upper()}:")
            for item in items[:5]:  # Show first 5
                print(f"  - {item['name']}")

def main():
    """Main processing function"""
    print("Starting zukan data processing...")
    process_and_save_data()
    print("Processing complete!")

if __name__ == "__main__":
    main()