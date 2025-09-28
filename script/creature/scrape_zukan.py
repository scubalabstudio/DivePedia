#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrape creature data from scuba-monsters.com/zukan/
Extract creature names from the encyclopedia page and nested pages
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin
import os

def scrape_zukan_main_page():
    """Scrape the main zukan page to find creature categories and links"""
    base_url = "https://scuba-monsters.com/zukan/"
    
    try:
        print("Fetching main zukan page...")
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for creature links and categories
        creature_links = []
        creature_names = []
        
        # Method 1: Look for direct creature names
        # Find links that might lead to creature pages
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            
            # Check if this looks like a creature page link
            if '/zukan/' in href and text and len(text) > 1:
                full_url = urljoin(base_url, href)
                creature_links.append({
                    'name': text,
                    'url': full_url
                })
        
        # Method 2: Look for creature names in text content
        # Find all text elements that might contain creature names
        for element in soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'li']):
            text = element.get_text(strip=True)
            
            # Skip navigation and common elements
            skip_words = ['ホーム', 'トップ', 'メニュー', 'ナビ', '検索', 'ログイン', 'サイト', 'モンスター']
            if any(word in text for word in skip_words):
                continue
                
            # Look for Japanese creature names (typically 2-10 characters)
            if text and 2 <= len(text) <= 10 and re.match(r'^[ひらがなカタカナ漢字ー]+$', text):
                creature_names.append(text)
        
        print(f"Found {len(creature_links)} creature links")
        print(f"Found {len(creature_names)} potential creature names")
        
        return creature_links, creature_names, soup
        
    except requests.RequestException as e:
        print(f"Error fetching main page: {e}")
        return [], [], None
    except Exception as e:
        print(f"Error parsing main page: {e}")
        return [], [], None

def scrape_creature_page(url, max_retries=3):
    """Scrape individual creature page for more names"""
    creatures = []
    
    for attempt in range(max_retries):
        try:
            print(f"Fetching {url} (attempt {attempt + 1})")
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for creature names in various elements
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'div', 'span', 'p', 'li']):
                text = element.get_text(strip=True)
                
                # Filter for potential creature names
                if text and 2 <= len(text) <= 15:
                    # Japanese creature name pattern
                    if re.match(r'^[ひらがなカタカナ漢字ー・（）]+$', text):
                        # Skip common words
                        skip_words = ['図鑑', 'ホーム', 'トップ', '検索', 'メニュー', 'ナビ', 'サイト']
                        if not any(word in text for word in skip_words):
                            creatures.append(text)
            
            return list(set(creatures))  # Remove duplicates
            
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

def categorize_creatures(creature_names):
    """Categorize creatures based on naming patterns"""
    categories = {
        'fish': [],
        'crustacean': [],
        'sea_slug': [],
        'other': []
    }
    
    # Fish patterns (many end with specific suffixes)
    fish_patterns = [
        r'.*[魚フグハゼダイキスイワシサバアジ]$',
        r'.*[ベラカワハギフエダイニザダイキンチャクダイスズメダイ]$',
        r'.*[チョウチョウウオハタネンブツダイ]$'
    ]
    
    # Crustacean patterns
    crustacean_patterns = [
        r'.*[エビカニヤドカリ]$',
        r'.*[ガニザリ]$'
    ]
    
    # Sea slug patterns
    sea_slug_patterns = [
        r'.*[ウミウシ]$',
        r'.*[ドーリス]$'
    ]
    
    for name in creature_names:
        categorized = False
        
        # Check fish patterns
        for pattern in fish_patterns:
            if re.match(pattern, name):
                categories['fish'].append(name)
                categorized = True
                break
        
        if not categorized:
            # Check crustacean patterns
            for pattern in crustacean_patterns:
                if re.match(pattern, name):
                    categories['crustacean'].append(name)
                    categorized = True
                    break
        
        if not categorized:
            # Check sea slug patterns
            for pattern in sea_slug_patterns:
                if re.match(pattern, name):
                    categories['sea_slug'].append(name)
                    categorized = True
                    break
        
        if not categorized:
            categories['other'].append(name)
    
    return categories

def save_creatures_data(categories, base_path="../../data/processed/creature/"):
    """Save categorized creature data to JSON files"""
    
    # Ensure directory exists
    os.makedirs(base_path, exist_ok=True)
    
    # Create data with IDs
    for category, names in categories.items():
        if not names:
            continue
            
        creatures_data = []
        for i, name in enumerate(sorted(set(names)), 1):
            creatures_data.append({
                "id": i,
                "name": name
            })
        
        filename = f"{base_path}zukan_{category}_data.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(creatures_data, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(creatures_data)} {category} creatures to {filename}")
        except Exception as e:
            print(f"Error saving {category} data: {e}")

def main():
    """Main function to scrape zukan data"""
    print("Starting zukan creature scraper...")
    
    # Scrape main page
    creature_links, main_page_names, soup = scrape_zukan_main_page()
    
    all_creature_names = set(main_page_names)
    
    # Scrape individual creature pages if found
    if creature_links:
        print(f"Scraping {len(creature_links)} creature pages...")
        for i, link_info in enumerate(creature_links[:20]):  # Limit to first 20 to avoid overload
            print(f"Processing {i+1}/{min(20, len(creature_links))}: {link_info['name']}")
            page_creatures = scrape_creature_page(link_info['url'])
            all_creature_names.update(page_creatures)
            time.sleep(1)  # Be polite to the server
    
    print(f"Total unique creature names found: {len(all_creature_names)}")
    
    # Categorize creatures
    categories = categorize_creatures(list(all_creature_names))
    
    # Print summary
    print("\nCategorization summary:")
    for category, names in categories.items():
        print(f"{category}: {len(names)} creatures")
    
    # Save data
    save_creatures_data(categories)
    
    # Also save all creatures in one file
    all_creatures = []
    creature_id = 1
    for category, names in categories.items():
        for name in sorted(set(names)):
            all_creatures.append({
                "id": creature_id,
                "name": name,
                "category": category
            })
            creature_id += 1
    
    all_filename = "../../data/processed/creature/zukan_all_creatures.json"
    try:
        with open(all_filename, 'w', encoding='utf-8') as f:
            json.dump(all_creatures, f, ensure_ascii=False, indent=2)
        print(f"Saved all {len(all_creatures)} creatures to {all_filename}")
    except Exception as e:
        print(f"Error saving all creatures data: {e}")

if __name__ == "__main__":
    main()