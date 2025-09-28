#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test scraper for scuba-monsters.com/zukan/ - small sample
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os

def test_group_page(group_id, group_name):
    """Test scraping a specific group page"""
    url = f"https://scuba-monsters.com/zukan/list/group/{group_id}/"
    
    try:
        print(f"Testing group {group_id} ({group_name}): {url}")
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        creatures = []
        
        # Method 1: Look for creature links
        creature_links = soup.find_all('a', href=re.compile(r'/zukan/species/\d+/'))
        print(f"  Found {len(creature_links)} creature links")
        
        for link in creature_links:
            name = link.get_text(strip=True)
            if name and 2 <= len(name) <= 25:
                creatures.append(name)
                print(f"    Link: {name}")
        
        # Method 2: Look in JavaScript data
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'japanese_name' in script.string:
                content = script.string
                names = re.findall(r'"japanese_name":"([^"]+)"', content)
                creatures.extend(names)
                print(f"  Found {len(names)} names in JavaScript")
                for name in names[:5]:  # Show first 5
                    print(f"    JS: {name}")
        
        # Method 3: Look for common creature name patterns in text
        all_text = soup.get_text()
        
        # Look for Japanese creature names
        japanese_names = re.findall(r'[ア-ン][ア-ンー・]{1,15}[魚エビカニウシダイハゼ]', all_text)
        print(f"  Found {len(japanese_names)} Japanese pattern names")
        for name in set(japanese_names[:5]):
            print(f"    Pattern: {name}")
        
        return list(set(creatures))
        
    except Exception as e:
        print(f"Error testing group {group_id}: {e}")
        return []

def main():
    """Test a few groups"""
    print("Testing zukan group pages...")
    
    # Test a few different types of groups
    test_groups = [
        (16, "ハゼ"),      # Popular fish group
        (19, "スズメダイ"),  # Another fish group  
        (26, "チョウチョウウオ"), # Colorful fish
        (47, "甲殻類"),    # Crustaceans
        (113, "ウミウシ・巻貝"), # Sea slugs
    ]
    
    all_creatures = []
    
    for group_id, group_name in test_groups:
        print(f"\n{'='*50}")
        creatures = test_group_page(group_id, group_name)
        
        for name in creatures:
            all_creatures.append({
                'id': len(all_creatures) + 1,
                'name': name,
                'group_id': group_id,
                'group_name': group_name
            })
        
        print(f"Total creatures from {group_name}: {len(creatures)}")
        time.sleep(1)  # Be polite
    
    print(f"\n{'='*50}")
    print(f"Grand total: {len(all_creatures)} creatures")
    
    # Remove duplicates
    seen = set()
    unique_creatures = []
    for creature in all_creatures:
        if creature['name'] not in seen:
            seen.add(creature['name'])
            unique_creatures.append(creature)
    
    print(f"Unique creatures: {len(unique_creatures)}")
    
    # Save test data
    if unique_creatures:
        os.makedirs("../../data/processed/creature/", exist_ok=True)
        filename = "../../data/processed/creature/zukan_test_sample.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(unique_creatures, f, ensure_ascii=False, indent=2)
        
        print(f"Saved test data to {filename}")
        
        # Show sample of what we found
        print("\nSample creatures found:")
        for creature in unique_creatures[:10]:
            print(f"  {creature['name']} (from {creature['group_name']})")

if __name__ == "__main__":
    main()