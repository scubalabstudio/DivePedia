#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix categorization of zukan creature data
"""

import json
import re
import os

def improved_categorize_creature(name):
    """Improved categorization logic"""
    
    # Crustacean patterns - check these first
    if re.search(r'(エビ|カニ|ヤドカリ|シャコ|ガニ|ザリ)', name):
        return 'crustacean'
    
    # Sea slug and mollusk patterns
    if re.search(r'(ウミウシ|アメフラシ|クリオネ|ガイ$|コチョウ|タマガイ|貝)', name):
        return 'sea_slug'
    
    # Other marine life patterns (not fish)
    if re.search(r'(クラゲ|イカ|タコ|ヒトデ|ウニ|ナマコ|サンゴ|イソギンチャク|ホヤ|クジラ|アザラシ|ラッコ|イルカ)', name):
        return 'other'
    
    # Fish patterns - most specific last
    if re.search(r'(ハゼ|ダイ|魚|フグ|キス|イワシ|サバ|アジ|マグロ|タイ|ベラ|カワハギ|フエダイ|ニザダイ|キンチャクダイ|スズメダイ|チョウチョウウオ|ハタ|ネンブツダイ|ヒメジ|アンコウ|エソ|ギンポ|アナゴ|ウツボ|カサゴ|コチ|ホウボウ|ブダイ|ボラ|カマス|ゴンベ|トラギス|カレイ|ヒラメ|キンメダイ|テンジクダイ)', name):
        return 'fish'
    
    # Default to other if none match
    return 'other'

def reprocess_creatures():
    """Reprocess creature categorization"""
    
    # Load the test data again
    with open("../../data/processed/creature/zukan_test_sample.json", 'r', encoding='utf-8') as f:
        creatures = json.load(f)
    
    print(f"Reprocessing {len(creatures)} creatures...")
    
    # Filter and recategorize
    valid_creatures = []
    categories = {'fish': [], 'crustacean': [], 'sea_slug': [], 'other': []}
    
    seen_names = set()
    
    for creature in creatures:
        name = creature['name']
        
        # Skip duplicates
        if name in seen_names:
            continue
        seen_names.add(name)
        
        # Skip obviously invalid entries
        if len(name) < 2 or len(name) > 30:
            continue
        
        # Skip common non-creature words
        skip_words = ['ホーム', 'メニュー', 'ナビ', 'サイト', '一覧', 'リスト', '検索', 'ページ']
        if any(word in name for word in skip_words):
            continue
        
        # Categorize
        category = improved_categorize_creature(name)
        
        creature_data = {'name': name, 'category': category}
        valid_creatures.append(creature_data)
        categories[category].append(creature_data)
    
    print(f"Valid unique creatures: {len(valid_creatures)}")
    
    # Print categorization summary
    print("\nFixed categorization summary:")
    for category, items in categories.items():
        print(f"{category}: {len(items)} creatures")
    
    # Save each category
    base_path = "../../data/processed/creature/"
    
    for category, items in categories.items():
        if items:
            # Assign IDs and clean format
            clean_items = []
            for i, item in enumerate(items, 1):
                clean_items.append({'id': i, 'name': item['name']})
            
            filename = f"{base_path}zukan_{category}_fixed.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(clean_items, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(clean_items)} {category} creatures to {filename}")
    
    # Save all creatures
    all_creatures = []
    creature_id = 1
    for category, items in categories.items():
        for item in items:
            all_creatures.append({
                'id': creature_id,
                'name': item['name'],
                'category': category
            })
            creature_id += 1
    
    all_filename = f"{base_path}zukan_all_fixed.json"
    with open(all_filename, 'w', encoding='utf-8') as f:
        json.dump(all_creatures, f, ensure_ascii=False, indent=2)
    print(f"Saved all {len(all_creatures)} creatures to {all_filename}")
    
    # Show samples
    print("\nSample creatures by category:")
    for category, items in categories.items():
        if items:
            print(f"\n{category.upper()} ({len(items)} total):")
            for item in items[:8]:  # Show first 8
                print(f"  - {item['name']}")

def main():
    print("Fixing creature categorization...")
    reprocess_creatures()
    print("Categorization fixed!")

if __name__ == "__main__":
    main()