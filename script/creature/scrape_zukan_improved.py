#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved scraper for scuba-monsters.com/zukan/
Extract creature names from group pages based on the discovered structure
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin
import os

def get_group_urls():
    """Get all group URLs from the main zukan page"""
    base_url = "https://scuba-monsters.com/zukan/"
    
    # Manually constructed list based on the debug output
    group_urls = []
    
    # Fish groups (1-38)
    fish_groups = [
        (1, "魚"), (2, "サメ・エイ"), (3, "ニシン・イワシ"), (4, "ウツボ・アナゴ"), (5, "エソ"),
        (6, "アンコウ"), (7, "タラ・サケ・ナマズ"), (8, "ダツ・サヨリ・トビウオ"), (9, "ヤガラ・ヨウジウオ"),
        (10, "カサゴ・カジカ"), (11, "コチ・ホウボウ"), (12, "キンメダイ"), (13, "ネズッポ"), (14, "ギンポ"),
        (15, "ニザダイ・アイゴ"), (16, "ハゼ"), (17, "サバ・マグロ"), (18, "ベラ"), (19, "スズメダイ"),
        (20, "ブダイ"), (21, "ボラ"), (22, "カマス"), (23, "ハタ・ハナダイ"), (24, "テンジクダイ・ハタンポ"),
        (25, "アジ・タカサゴ"), (26, "チョウチョウウオ"), (27, "キンチャクダイ"), (28, "ヒメジ"),
        (29, "タイ・フエダイ・フエフキダイ"), (30, "イサキ・コショウダイ"), (31, "イトヨリダイ・タマガシラ"),
        (32, "ゴンベ・タカノハダイ"), (33, "トラギス・ミシマオコゼ"), (34, "アカマンボウ"), (35, "ウバウオ"),
        (36, "カレイ・ヒラメ"), (37, "フグ・カワハギ"), (38, "その他")
    ]
    
    # Mammal groups (39-43)
    mammal_groups = [
        (39, "哺乳類"), (40, "ラッコ"), (41, "アシカ・アザラシ"), (42, "ジュゴン"), (43, "イルカ・クジラ")
    ]
    
    # Reptile/bird groups (44-46)
    reptile_groups = [
        (44, "爬虫類・鳥類"), (45, "ウミヘビ"), (46, "ウミガメ")
    ]
    
    # Crustacean groups (47-77)
    crustacean_groups = [
        (47, "甲殻類"), (48, "オキアミ"), (49, "アミ"), (50, "シャコ"), (51, "ヨコエビ"), (52, "ワレカラ"),
        (53, "クルマエビ"), (54, "イセエビ・セミエビ"), (55, "ワラエビ"), (56, "コシオリエビ"), (57, "カニダマシ"),
        (58, "ヤドカリ"), (59, "オトヒメエビ"), (60, "カイカムリ"), (61, "イワガニ"), (62, "クモガニ"),
        (63, "スナガニ"), (64, "ワタリガニ"), (65, "カラッパ"), (66, "アサヒガニ"), (67, "ケブカガニ・ゴカクガニ"),
        (68, "オウギガニ"), (69, "コブシガニ"), (70, "その他カニ"), (71, "テッポウエビ"), (72, "モエビ"),
        (73, "ツノメエビ"), (74, "タラバエビ"), (75, "テナガエビ"), (76, "その他エビ"), (77, "その他甲殻類")
    ]
    
    # Sea slug and mollusk groups (113-141)
    mollusk_groups = [
        (113, "ウミウシ・巻貝"), (114, "カサガイ"), (115, "アメフラシ"), (116, "クリオネ"),
        (117, "シイノミガイ・ミスガイ"), (118, "ミノウミウシ"), (119, "キセワタ・ウミコチョウ・アワツブガイ"),
        (120, "スギノハウミウシ"), (121, "タテジマウミウシ"), (122, "イロウミウシ"), (123, "フジタウミウシ"),
        (124, "イボウミウシ・クロシタナシウミウシ"), (125, "ミドリガイ"), (126, "フシエラガイ"),
        (127, "その他ウミウシ"), (128, "タカラガイ"), (129, "イモガイ"), (130, "ホラガイ"), (131, "エゾバイ"),
        (132, "アッキガイ"), (133, "ニシキウズガイ"), (134, "その他ウミウシ・巻貝"), (135, "二枚貝"),
        (136, "イタヤガイ"), (137, "イガイ"), (138, "カキ"), (139, "ハマグリ"), (140, "フネガイ"),
        (141, "その他二枚貝")
    ]
    
    # Other important groups
    other_groups = [
        (78, "ホヤ・タリア"), (82, "クラゲ・ヒドロ虫"), (91, "イカ・タコ"), (98, "棘皮動物"),
        (99, "ヒトデ"), (100, "ウミユリ・ウミシダ"), (101, "ウニ"), (102, "ナマコ"),
        (103, "サンゴ・イソギンチャク"), (104, "イソギンチャク"), (142, "海綿"),
        (144, "両生類"), (147, "ヒラムシ"), (150, "鳥"), (151, "植物"), (152, "海藻"),
        (153, "海草"), (155, "ゴカイ")
    ]
    
    all_groups = fish_groups + mammal_groups + reptile_groups + crustacean_groups + mollusk_groups + other_groups
    
    for group_id, group_name in all_groups:
        url = f"https://scuba-monsters.com/zukan/list/group/{group_id}/"
        group_urls.append((group_id, group_name, url))
    
    return group_urls

def scrape_group_page(group_id, group_name, url, max_retries=3):
    """Scrape individual group page for creature names"""
    creatures = []
    
    for attempt in range(max_retries):
        try:
            print(f"Fetching group {group_id} ({group_name}): {url} (attempt {attempt + 1})")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Method 1: Look for creature links/names in list format
            # Many creature pages have links like /zukan/species/[id]/
            creature_links = soup.find_all('a', href=re.compile(r'/zukan/species/\d+/'))
            for link in creature_links:
                name = link.get_text(strip=True)
                if name and 2 <= len(name) <= 25:
                    creatures.append(name)
            
            # Method 2: Look in common creature display elements
            creature_elements = soup.find_all(['div', 'span', 'li', 'h3', 'h4'], 
                                            class_=re.compile(r'name|title|creature|species'))
            for elem in creature_elements:
                text = elem.get_text(strip=True)
                if text and 2 <= len(text) <= 25 and re.match(r'^[ひらがなカタカナ漢字ー・（）\w\s]+$', text):
                    # Skip common navigation words
                    skip_words = ['ホーム', 'メニュー', 'ナビ', '検索', '図鑑', 'サイト', 'ページ', '一覧', 'リスト']
                    if not any(word in text for word in skip_words):
                        creatures.append(text)
            
            # Method 3: Look for JavaScript data
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    content = script.string
                    # Look for creature data in JavaScript
                    if 'japanese_name' in content or 'scientific_name' in content:
                        # Extract creature names from JSON-like data
                        import re
                        names = re.findall(r'"japanese_name":"([^"]+)"', content)
                        creatures.extend(names)
            
            # Remove duplicates
            unique_creatures = list(set(creatures))
            print(f"  Found {len(unique_creatures)} creatures in group {group_name}")
            
            return unique_creatures
            
        except requests.RequestException as e:
            print(f"Request error for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return []
        except Exception as e:
            print(f"Parse error for {url}: {e}")
            return []
    
    return []

def categorize_creature(name):
    """Categorize a creature based on its name"""
    
    # Fish patterns
    fish_patterns = [
        r'.*[魚フグハゼダイキスイワシサバアジマグロタイ]$',
        r'.*[ベラカワハギフエダイニザダイキンチャクダイスズメダイ]$',
        r'.*[チョウチョウウオハタネンブツダイヒメジアンコウ]$',
        r'.*[エソギンポイワシアナゴウツボカサゴ]$',
        r'.*[ブダイボラカマスコチホウボウ]$'
    ]
    
    # Crustacean patterns
    crustacean_patterns = [
        r'.*[エビカニヤドカリシャコ]$',
        r'.*[ガニザリ]$',
        r'.*(オキアミ|アミ|ヨコエビ|ワレカラ).*'
    ]
    
    # Sea slug patterns  
    sea_slug_patterns = [
        r'.*ウミウシ.*',
        r'.*アメフラシ.*',
        r'.*クリオネ.*',
        r'.*ミノウミウシ.*'
    ]
    
    # Other marine life patterns
    other_patterns = [
        r'.*[クラゲイカタコ].*',
        r'.*[ヒトデウニナマコ].*',
        r'.*[サンゴイソギンチャク].*',
        r'.*[ホヤクジラアザラシ].*'
    ]
    
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
    
    # Default categorization based on group context
    return 'other'

def save_creatures_by_category(all_creatures, base_path="../../data/processed/creature/"):
    """Save creatures categorized by type"""
    
    os.makedirs(base_path, exist_ok=True)
    
    # Categorize all creatures
    categories = {'fish': [], 'crustacean': [], 'sea_slug': [], 'other': []}
    
    for creature in all_creatures:
        name = creature['name']
        category = categorize_creature(name)
        categories[category].append(creature)
    
    # Save each category
    for category, creatures in categories.items():
        if creatures:
            # Re-assign IDs within category
            for i, creature in enumerate(creatures, 1):
                creature['id'] = i
            
            filename = f"{base_path}zukan_{category}_data.json"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(creatures, f, ensure_ascii=False, indent=2)
                print(f"Saved {len(creatures)} {category} creatures to {filename}")
            except Exception as e:
                print(f"Error saving {category} data: {e}")
    
    return categories

def main():
    """Main function to scrape all zukan data"""
    print("Starting comprehensive zukan creature scraper...")
    
    # Get all group URLs
    group_urls = get_group_urls()
    print(f"Found {len(group_urls)} groups to scrape")
    
    all_creatures = []
    creature_id = 1
    
    # Scrape each group (limit to avoid overwhelming the server)
    for i, (group_id, group_name, url) in enumerate(group_urls[:50]):  # First 50 groups
        print(f"\nProcessing group {i+1}/{min(50, len(group_urls))}: {group_name}")
        
        group_creatures = scrape_group_page(group_id, group_name, url)
        
        # Add to master list with IDs
        for name in group_creatures:
            all_creatures.append({
                'id': creature_id,
                'name': name,
                'group_id': group_id,
                'group_name': group_name
            })
            creature_id += 1
        
        # Be polite to the server
        time.sleep(1)
    
    print(f"\nTotal creatures found: {len(all_creatures)}")
    
    # Remove duplicates by name (keep first occurrence)
    seen_names = set()
    unique_creatures = []
    for creature in all_creatures:
        if creature['name'] not in seen_names:
            seen_names.add(creature['name'])
            unique_creatures.append(creature)
    
    print(f"Unique creatures after deduplication: {len(unique_creatures)}")
    
    # Re-assign IDs after deduplication
    for i, creature in enumerate(unique_creatures, 1):
        creature['id'] = i
    
    # Save all creatures
    all_filename = "../../data/processed/creature/zukan_all_creatures.json"
    try:
        with open(all_filename, 'w', encoding='utf-8') as f:
            json.dump(unique_creatures, f, ensure_ascii=False, indent=2)
        print(f"Saved all {len(unique_creatures)} creatures to {all_filename}")
    except Exception as e:
        print(f"Error saving all creatures: {e}")
    
    # Save by category
    categories = save_creatures_by_category(unique_creatures)
    
    # Print summary
    print("\nFinal summary:")
    for category, creatures in categories.items():
        print(f"{category}: {len(creatures)} creatures")

if __name__ == "__main__":
    main()